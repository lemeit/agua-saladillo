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

## Datos y estado actual

Por ahora es un **prototipo standalone**: un único archivo HTML sin build ni backend propio. Los registros (87 muestras, mayo 2025 – abril 2026, 52 puntos únicos) están embebidos como un array JS (`RAW`) dentro del propio `index.html`, y las coordenadas cargadas manualmente en el panel "Ubicaciones" se guardan en `localStorage` del navegador (no persisten entre dispositivos ni se comparten entre usuarios).

## Roadmap

Ideas para evolucionar este proyecto al mismo nivel que EMA y AQ:

- **Backend propio (Cloudflare D1 + Worker + GitHub Actions)**: reemplazar el array `RAW` embebido y el `localStorage` de coordenadas por una base de datos real, siguiendo el mismo patrón de ingesta que ya usan `ema-saladillo` y `purpleair-saladillo`.
- **Adoptar el sistema de diseño compartido** (`lemeit-theme.css` / `lemeit-common.js` de design.lemeit.ar): hoy el dashboard usa su propia paleta oscura estilo GitHub (`--accent:#58a6ff`, tipografía `system-ui`), independiente de la identidad visual de EMA/AQ. Unificar tipografía, paleta y componentes (header, footer, badges) es el paso pendiente más importante antes de publicarlo en `wq.lemeit.ar`.
- **Footer con versión + selector de portales**, igual que EMA y AQ (`LemeitCommon.renderFooter` / `initSwitcher`).
- Favicon ya definido y aplicado: monograma **"WQ"** en teal `#4FB0C6`, mismo patrón que EMA (celeste) y AQ (naranja).
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
