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

## Diseño

Ya adopta el sistema de diseño compartido de [design.lemeit.ar](https://design.lemeit.ar) (`lemeit-theme.css` + `lemeit-common.js`): misma paleta y tipografía (JetBrains Mono) que EMA y AQ, header con badge **WQ**, selector de portales y footer versionado (`LemeitCommon.initSwitcher` / `renderFooter`). El resto de los componentes (tabs, tarjetas, tabla, panel de administración) mantiene su propio CSS local, igual que en los otros dos proyectos — solo las variables de color/tipografía están unificadas.

## Roadmap

- **Backend propio (Cloudflare D1 + Worker + GitHub Actions)**: reemplazar el array `RAW` embebido y el `localStorage` de coordenadas por una base de datos real, siguiendo el mismo patrón de ingesta que ya usan `ema-saladillo` y `purpleair-saladillo`.
- **Actualización de datos**: hoy es 100% manual. Una posibilidad a futuro es un job (GitHub Actions, cron mensual) que revise las páginas `analisis_2025`/`analisis_2026` del sitio municipal y avise si aparecieron PDF nuevos para transcribir — no hay forma de saber la frecuencia de publicación de antemano, así que por ahora esto queda como idea, no implementado.
- Deploy en Cloudflare Pages (`wrangler pages deploy . --project-name=agua-saladillo`) apuntado a `wq.lemeit.ar`.

## Red de monitoreo ambiental

- **Meteorología** — [emas.lemeit.ar](https://emas.lemeit.ar)
- **Calidad del aire** — [aq.lemeit.ar](https://aq.lemeit.ar)
- **Calidad del agua** — este proyecto (en desarrollo)

## Proyecto educativo

Ing. Luciano Lamaita — docente de Física y Química en Saladillo, Buenos Aires — más proyectos y materiales en [profe.lemeit.ar](https://profe.lemeit.ar)

## Licencia

Datos: monitoreo municipal de calidad de agua, uso educativo/informativo.
Código: MIT.
