# Calidad del Agua — Saladillo

Monitoreo de calidad de agua de red en Saladillo, Buenos Aires, Argentina: arsénico, nitratos, nitritos, fluoruro, metales pesados y parámetros bacteriológicos (coliformes totales, *Escherichia coli*, *Pseudomona aeruginosa*) sobre decenas de puntos de la red municipal (bombas, escuelas, jardines de infantes, domicilios). Pensado para publicarse en [wq.lemeit.ar](https://wq.lemeit.ar).

Es uno de tres proyectos de monitoreo ambiental que comparten la misma infraestructura de Cloudflare (Pages + Workers + D1), pensados para integrarse a futuro: [emas.lemeit.ar](https://emas.lemeit.ar) (meteorología), [aq.lemeit.ar](https://aq.lemeit.ar) (calidad del aire, sensores PurpleAir) y este (calidad del agua).

## Origen

Este dashboard existía como un archivo suelto (`docs/agua_saladillo.html`) dentro del repo de `ema-saladillo`, sin repositorio propio. Se migró a este repo dedicado en agosto de 2026 para poder evolucionarlo de forma independiente, igual que los otros dos proyectos hermanos.

## Funcionalidad

- **Resumen**: filtros globales (tipo de punto, rango de fechas, estado), tarjetas de estadísticas (muestras, puntos únicos, % de arsénico sobre límite, nitratos, fluoruro, *E. Coli* detectada) y alertas automáticas cuando un parámetro supera el límite normativo.
- **Por punto / Parámetros**: vistas desagregadas por fuente y por parámetro.
- **Mapa**: puntos de muestreo geolocalizados (Leaflet), con ficha de detalle por punto.
- **Tabla**: histórico completo, ordenable por columna.
- **Normativa**: tabla comparativa contra los límites del Código Alimentario Argentino (Cap. XII) y la Ley PBA 11.820.
- **Ubicaciones** (panel de administración): permite cargar/editar coordenadas de los puntos de muestreo que todavía no las tienen.

## Datos y origen

Por ahora es un **prototipo standalone**: un único archivo HTML sin build ni backend propio. Los registros (87 muestras, mayo 2025 – abril 2026, 52 puntos únicos) están embebidos como un array JS (`RAW`) dentro del propio `index.html`, y las coordenadas cargadas manualmente en el panel "Ubicaciones" se guardan en `localStorage` del navegador (no persisten entre dispositivos ni se comparten entre usuarios).

Los valores salen de los protocolos de ensayo (análisis de agua) que la Municipalidad de Saladillo publica como PDF sueltos en su sitio:

- [saladillo.gob.ar/?q=analisis_2025](https://www.saladillo.gob.ar/?q=analisis_2025) — ~60 protocolos
- [saladillo.gob.ar/?q=analisis_2026](https://www.saladillo.gob.ar/?q=analisis_2026) — ~43 protocolos (se sigue subiendo material, sin frecuencia ni orden fijo)

No hay tabla, índice ni nombres de archivo consistentes en ninguna de las dos páginas (algunos PDF se llaman `PROTOCOLO XXXXX`, otros `informe_1_N.pdf`, sin fecha en el nombre) — la carga a `RAW` fue manual, transcribiendo protocolo por protocolo. Es la fuente real, pero no una API ni nada remotamente automatizable tal como está publicada hoy.

### Cobertura de parámetros (agosto 2026)

`RAW` incluye hoy los 30 parámetros presentes en los protocolos transcriptos (metales pesados, plaguicidas organoclorados, trihalometanos, VOCs y bacteriología), no solo los 9 originales. `LIM` (límites CAA/PBA) cubre 31 parámetros — las vistas "Parámetros" y "Mapa" son genéricas y muestran cualquier parámetro presente en `LIM` sin cambios de código. La vista "Tabla" sigue mostrando un subconjunto curado de columnas por legibilidad; el botón **⬇ CSV** exporta el dataset completo (metadata + los 31 parámetros + bacteriología).

Pendiente (no incluido aún): metadata completa por protocolo (laboratorio, número de protocolo, cadena de custodia, hora de extracción) — los datos actuales solo tienen fuente, fecha y archivo de origen, porque la extracción CSV usada como base no capturó esos campos. La ingesta automatizada (ver "Ingesta automática de protocolos" abajo) sí captura esos campos para los protocolos nuevos a partir de agosto 2026, pero integrarlos al histórico de `RAW` sigue siendo manual.

**Nota sobre límites de referencia**: el límite de PBA para Arsénico embebido en `LIM` (0.010 mg/L) reproduce el que citan los protocolos municipales, pero el texto vigente de la Ley PBA 11.820 (Anexo A) verificado en agosto 2026 indica 0.05 mg/L para ese parámetro. Se mantiene el valor de los protocolos por ahora — es una discrepancia real entre fuente primaria y práctica de laboratorio, no un error de carga, y conviene revisarla con la Municipalidad.

## Diseño

Ya adopta el sistema de diseño compartido de [design.lemeit.ar](https://design.lemeit.ar) (`lemeit-theme.css` + `lemeit-common.js`): misma paleta y tipografía (JetBrains Mono) que EMA y AQ, header con badge **WQ**, selector de portales y footer versionado (`LemeitCommon.initSwitcher` / `renderFooter`). El resto de los componentes (tabs, tarjetas, tabla, panel de administración) mantiene su propio CSS local, igual que en los otros dos proyectos — solo las variables de color/tipografía están unificadas.

## Ingesta automática de protocolos

Desde agosto de 2026 hay un GitHub Action (`.github/workflows/protocolos-ingest.yml`) que automatiza la parte más pesada de bajar y leer protocolos nuevos — **se dispara a mano** desde la pestaña Actions del repo (`workflow_dispatch`), no corre solo por cron, para mantener control sobre cuándo se ejecuta.

Qué hace:

1. **`scripts/descargar_protocolos.py`** — recorre `analisis_2025` y `analisis_2026`, y descarga a `protocolos/<año>/` los PDF que todavía no están en el repo ni en `protocolos/manifest_historico.json` (la lista de los 87 protocolos que ya se integraron a mano al dashboard antes de que existiera esta carpeta, para no volver a bajarlos).
2. **`scripts/extraer_datos.py`** — por cada PDF nuevo, le pide a la API de Gemini (gratis, lee el PDF directo, sin OCR previo) que devuelva JSON estructurado: número de protocolo, fecha y hora de muestreo, punto de extracción, quién tomó la muestra, y la tabla completa de determinaciones con valor/unidad/método/límites citados en el propio protocolo. Los protocolos municipales no tienen un formato de tabla único (fisicoquímica, bacteriología y metales/plaguicidas usan columnas distintas), así que se usa un modelo en vez de un parser rígido — cada extracción incluye su propio nivel de confianza declarado.
3. Todo lo extraído se agrega a **`protocolos/extraidos_pendientes.csv`** (nunca a `index.html` directamente). Revisar y mergear al dashboard sigue siendo una decisión humana — la extracción automática de PDF con formato variable puede equivocarse, así que no hay que confiar en ella a ciegas. Si algún PDF no se pudo leer, queda marcado con `confianza: baja` y una nota explicando por qué, en vez de fallar en silencio.
4. Se commitea todo (PDFs + CSV de pendientes) directo a la rama por la Action.

Para activarlo hace falta un secret `GEMINI_API_KEY` en la configuración del repo (Settings → Secrets and variables → Actions) — se consigue gratis en [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Roadmap

- **Mergear `extraidos_pendientes.csv` al histórico**: falta el paso (todavía manual) de revisar lo que junta la ingesta automática e incorporarlo a `RAW`/`LIM`.
- **Backend propio (Cloudflare D1 + Worker)**: reemplazar el array `RAW` embebido y el `localStorage` de coordenadas por una base de datos real, siguiendo el mismo patrón que ya usan `ema-saladillo` y `purpleair-saladillo` — recién ahí tendría sentido que la ingesta escriba directo a la base en vez de a un CSV de staging.
- **Fisicoquímica completa (Tabla I)**: pH, dureza, cloruros, sulfatos, color, turbiedad, olor, alcalinidad, sólidos disueltos, amonio, calcio, magnesio — están en los protocolos pero todavía no en `LIM`/`RAW`; requiere curar el CSV crudo (`COMPLETO.csv`) o esperar a que la ingesta automática junte suficientes protocolos nuevos con esos campos.
- Deploy en Cloudflare Pages (`wrangler pages deploy . --project-name=agua-saladillo`) apuntado a `wq.lemeit.ar` — **ya en producción** desde agosto 2026.

## Red de monitoreo ambiental

- **Meteorología** — [emas.lemeit.ar](https://emas.lemeit.ar)
- **Calidad del aire** — [aq.lemeit.ar](https://aq.lemeit.ar)
- **Calidad del agua** — este proyecto (en desarrollo)

## Proyecto educativo

Ing. Luciano Lamaita — docente de Física y Química en Saladillo, Buenos Aires — más proyectos y materiales en [profe.lemeit.ar](https://profe.lemeit.ar)

## Licencia

Datos: monitoreo municipal de calidad de agua, uso educativo/informativo.
Código: MIT.
