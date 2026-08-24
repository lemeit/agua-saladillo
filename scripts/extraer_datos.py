#!/usr/bin/env python3
"""
Extrae los datos estructurados de los PDF nuevos (los que dejó
descargar_protocolos.py en protocolos/<año>/ y todavía no figuran en
protocolos/manifest_procesados.json) usando la API de Gemini, que lee el PDF
directamente — no hace falta OCR ni extracción de texto previa.

Los protocolos municipales NO tienen un formato de tabla único (fisicoquímica,
bacteriología y metales/plaguicidas usan columnas distintas), así que en vez
de un parser rígido por posición de columna, se le pide a Gemini que devuelva
JSON con un esquema fijo pensado para cubrir cualquiera de esos formatos.

Importante: este script NUNCA escribe en index.html. Todo lo extraído queda
en protocolos/extraidos_pendientes.csv para revisión humana antes de
integrarlo al dashboard — la extracción automática de PDF con formato
variable puede equivocarse, así que no hay que confiar en ella a ciegas.
"""
import base64
import csv
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PROTOCOLOS_DIR = ROOT / "protocolos"
MANIFEST_PROCESADOS = PROTOCOLOS_DIR / "manifest_procesados.json"
STAGING_CSV = PROTOCOLOS_DIR / "extraidos_pendientes.csv"

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

PROMPT = """Sos un extractor de datos para protocolos de análisis de agua potable \
publicados por un municipio argentino. Te paso UN PDF con UN protocolo/informe de \
laboratorio. Los protocolos NO tienen un formato único: pueden tener una tabla de \
fisicoquímica (columnas tipo Parámetro/Valor/Unidad/O.M.S./C.A.A./Método), una tabla \
de bacteriología (DETERMINACIÓN/RESULTADO/U.M./LOD/MÉTODO/LÍMITE CAA), o una tabla de \
metales pesados y plaguicidas. Puede haber también más de una tabla en el mismo PDF.

Devolvé SOLO un objeto JSON (sin texto adicional, sin markdown) con este esquema exacto:

{
  "protocolo_numero": "string o null - el número de protocolo/informe si aparece",
  "fecha_reporte": "YYYY-MM-DD o null - fecha de emisión del informe",
  "fuente": "string o null - el punto/sitio de muestreo (ej: BOMBA 1, JARDIN Nº4)",
  "recolectado_por": "string o null - quién tomó la muestra",
  "fecha_muestra": "YYYY-MM-DD o null - fecha en que se tomó la muestra (puede ser distinta a fecha_reporte)",
  "hora_muestra": "HH:MM o null",
  "observaciones": "string o null - la conclusión/veredicto (ej: POTABLE, Bacteriológicamente Potable)",
  "determinaciones": [
    {
      "nombre": "string - el nombre EXACTO del parámetro tal como aparece en el PDF, sin traducir ni normalizar",
      "valor_texto": "string - el valor tal cual aparece (puede ser texto no numérico: Ausencia, SIN OLORES, —, etc.)",
      "valor_numerico": "number o null - el valor como número si es claramente numérico, si no null",
      "unidad": "string o null",
      "metodo": "string o null - método analítico si aparece (ej: SM 2120 C)",
      "limite_oms": "number o null - límite de referencia OMS si la tabla trae esa columna",
      "limite_caa": "number o null - límite de referencia CAA si la tabla trae esa columna",
      "lod": "number o null - límite de detección si aparece"
    }
  ],
  "extraccion_confianza": "alta, media o baja - tu propia evaluación de qué tan seguro estás de haber leído todo bien",
  "extraccion_nota": "string o null - cualquier cosa rara, ambigua, o que no pudiste leer bien (letra ilegible, tabla cortada, etc.)"
}

Si el PDF no es un protocolo de análisis de agua reconocible, devolvé determinaciones \
como lista vacía y extraccion_confianza "baja" con la razón en extraccion_nota. \
No inventes valores: si algo no está o no se lee, usá null. Preferí null y una nota \
antes que adivinar."""


def cargar_procesados():
    if MANIFEST_PROCESADOS.exists():
        return json.loads(MANIFEST_PROCESADOS.read_text(encoding="utf-8"))
    return {}


def listar_pdfs_pendientes(procesados):
    pendientes = []
    for pdf in sorted(PROTOCOLOS_DIR.glob("20*/*.pdf")):
        rel = str(pdf.relative_to(ROOT))
        if rel not in procesados:
            pendientes.append(pdf)
    return pendientes


def extraer_con_gemini(pdf_path, intentos=3):
    data_b64 = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
    body = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "application/pdf", "data": data_b64}},
                {"text": PROMPT},
            ]
        }],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            r = requests.post(GEMINI_URL, json=body, timeout=90)
            if r.status_code == 429:
                espera = 20 * intento
                print(f"  Rate limit, esperando {espera}s...")
                time.sleep(espera)
                continue
            r.raise_for_status()
            payload = r.json()
            texto = payload["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(texto)
        except Exception as e:  # noqa: BLE001 - queremos capturar cualquier falla y marcar revisión manual
            ultimo_error = e
            time.sleep(5)
    raise RuntimeError(f"No se pudo extraer tras {intentos} intentos: {ultimo_error}")


def filas_csv_de(pdf_rel, extraido):
    base = {
        "archivo": pdf_rel,
        "protocolo_numero": extraido.get("protocolo_numero"),
        "fecha_reporte": extraido.get("fecha_reporte"),
        "fuente": extraido.get("fuente"),
        "recolectado_por": extraido.get("recolectado_por"),
        "fecha_muestra": extraido.get("fecha_muestra"),
        "hora_muestra": extraido.get("hora_muestra"),
        "observaciones": extraido.get("observaciones"),
        "confianza": extraido.get("extraccion_confianza"),
        "nota_extraccion": extraido.get("extraccion_nota"),
    }
    dets = extraido.get("determinaciones") or []
    if not dets:
        yield {**base, "determinacion": None, "valor_texto": None, "valor_numerico": None,
               "unidad": None, "metodo": None, "limite_oms": None, "limite_caa": None, "lod": None}
        return
    for d in dets:
        yield {
            **base,
            "determinacion": d.get("nombre"),
            "valor_texto": d.get("valor_texto"),
            "valor_numerico": d.get("valor_numerico"),
            "unidad": d.get("unidad"),
            "metodo": d.get("metodo"),
            "limite_oms": d.get("limite_oms"),
            "limite_caa": d.get("limite_caa"),
            "lod": d.get("lod"),
        }


CSV_COLS = ["archivo", "protocolo_numero", "fecha_reporte", "fuente", "recolectado_por",
            "fecha_muestra", "hora_muestra", "determinacion", "valor_texto", "valor_numerico",
            "unidad", "metodo", "limite_oms", "limite_caa", "lod", "observaciones",
            "confianza", "nota_extraccion"]


def main():
    if not GEMINI_API_KEY:
        print("ERROR: falta GEMINI_API_KEY en el ambiente.", file=sys.stderr)
        sys.exit(1)

    procesados = cargar_procesados()
    pendientes = listar_pdfs_pendientes(procesados)
    print(f"PDF pendientes de extraer: {len(pendientes)}")
    if not pendientes:
        return

    filas_nuevas = []
    for pdf in pendientes:
        rel = str(pdf.relative_to(ROOT))
        print(f"Extrayendo {rel}...")
        try:
            extraido = extraer_con_gemini(pdf)
            n_det = len(extraido.get("determinaciones") or [])
            confianza = extraido.get("extraccion_confianza", "?")
            print(f"  OK — {n_det} determinaciones, confianza: {confianza}")
            procesados[rel] = {"ok": True, "confianza": confianza}
        except Exception as e:  # noqa: BLE001
            print(f"  FALLÓ: {e}", file=sys.stderr)
            extraido = {
                "determinaciones": [],
                "extraccion_confianza": "baja",
                "extraccion_nota": f"Extracción automática falló: {e}. Revisar el PDF a mano.",
            }
            procesados[rel] = {"ok": False, "error": str(e)}
        filas_nuevas.extend(filas_csv_de(rel, extraido))
        time.sleep(4)  # tier gratis: 15 req/min — de sobra de margen para no pegarle al límite

    existe = STAGING_CSV.exists()
    with open(STAGING_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if not existe:
            w.writeheader()
        for fila in filas_nuevas:
            w.writerow(fila)

    MANIFEST_PROCESADOS.write_text(json.dumps(procesados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(filas_nuevas)} filas agregadas a {STAGING_CSV.relative_to(ROOT)}")
    print("Recordá: nada de esto entra al dashboard solo. Hay que revisar y mergear a mano.")


if __name__ == "__main__":
    main()
