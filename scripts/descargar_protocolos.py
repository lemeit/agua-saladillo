#!/usr/bin/env python3
"""
Descarga PDFs nuevos de protocolos de análisis de agua publicados por la
Municipalidad de Saladillo (https://www.saladillo.gob.ar/?q=analisis_2025 y
?q=analisis_2026), evitando volver a bajar los que ya están en el repo o los
que ya fueron integrados manualmente al dashboard antes de que existiera esta
carpeta (ver protocolos/manifest_historico.json).

Corre solo por disparo manual (workflow_dispatch) — ver
.github/workflows/protocolos-ingest.yml. No modifica index.html: solo deja
los PDF nuevos en protocolos/<año>/ para que extraer_datos.py los procese.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.saladillo.gob.ar"
LISTADOS = {
    "2025": f"{BASE}/?q=analisis_2025",
    "2026": f"{BASE}/?q=analisis_2026",
}
ROOT = Path(__file__).resolve().parent.parent
PROTOCOLOS_DIR = ROOT / "protocolos"
MANIFEST_HISTORICO = PROTOCOLOS_DIR / "manifest_historico.json"
HEADERS = {"User-Agent": "agua-saladillo-bot/1.0 (+https://wq.lemeit.ar)"}


def cargar_conocidos():
    """Nombres de archivo que NO hay que volver a bajar: los ya integrados
    manualmente antes de que existiera esta carpeta, más los que ya están
    físicamente en protocolos/<año>/ de una corrida anterior."""
    conocidos = set()
    if MANIFEST_HISTORICO.exists():
        conocidos.update(json.loads(MANIFEST_HISTORICO.read_text(encoding="utf-8")))
    for year_dir in PROTOCOLOS_DIR.glob("20*"):
        if year_dir.is_dir():
            conocidos.update(p.name for p in year_dir.glob("*.pdf"))
    return conocidos


def listar_pdfs(url):
    """Devuelve [(nombre_archivo, url_absoluta), ...] de una página de listado."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    encontrados = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            abs_url = urljoin(BASE, href)
            nombre = abs_url.rsplit("/", 1)[-1]
            encontrados.append((nombre, abs_url))
    return encontrados


def main():
    conocidos = cargar_conocidos()
    print(f"Ya conocidos (no se re-descargan): {len(conocidos)}")

    nuevos_totales = []
    for anio, listado_url in LISTADOS.items():
        destino = PROTOCOLOS_DIR / anio
        destino.mkdir(parents=True, exist_ok=True)
        try:
            pdfs = listar_pdfs(listado_url)
        except requests.RequestException as e:
            print(f"[{anio}] ERROR al listar {listado_url}: {e}", file=sys.stderr)
            continue
        print(f"[{anio}] {len(pdfs)} PDF listados en la página municipal")

        vistos_este_listado = set()
        for nombre, url in pdfs:
            if nombre in vistos_este_listado:
                continue  # duplicado dentro del mismo listado (pasa seguido, ver README)
            vistos_este_listado.add(nombre)
            if nombre in conocidos:
                continue
            destino_pdf = destino / nombre
            try:
                resp = requests.get(url, headers=HEADERS, timeout=60)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"[{anio}] ERROR bajando {url}: {e}", file=sys.stderr)
                continue
            destino_pdf.write_bytes(resp.content)
            conocidos.add(nombre)
            nuevos_totales.append(str(destino_pdf.relative_to(ROOT)))
            print(f"[{anio}] Nuevo: {nombre}")

    print(f"\nTotal PDF nuevos descargados: {len(nuevos_totales)}")
    # Lo consume extraer_datos.py y también el step de GitHub Actions para el resumen del commit.
    (PROTOCOLOS_DIR / "_nuevos_ultima_corrida.json").write_text(
        json.dumps(nuevos_totales, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
