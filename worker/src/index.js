/**
 * API de coordenadas para agua-saladillo, sobre Cloudflare D1.
 *
 * Reemplaza el localStorage por navegador que usaba el panel "⚙ Ubicaciones":
 * ahora las coordenadas son un dato compartido, y solo se pueden escribir
 * con una clave de administrador (secret ADMIN_KEY, configurado con
 * `wrangler secret put ADMIN_KEY` — nunca en este archivo ni en wrangler.toml).
 *
 * Endpoints:
 *   GET  /api/coords   -> público. { "<fuente>": {lat, lon, tipo, dir}, ... }
 *   POST /api/coords   -> protegido. Header "X-Admin-Key" debe matchear el
 *                         secret ADMIN_KEY. Body JSON: { fuente, lat, lon, tipo, dir }.
 *                         Hace upsert (INSERT ... ON CONFLICT UPDATE) por "fuente".
 *                         Para "borrar" coordenadas se manda lat/lon en null.
 */

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, X-Admin-Key",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    if (url.pathname !== "/api/coords") {
      return json({ error: "Not found" }, 404);
    }

    try {
      if (request.method === "GET") {
        const { results } = await env.DB.prepare(
          "SELECT fuente, lat, lon, tipo, dir FROM coords"
        ).all();
        const out = {};
        for (const r of results) {
          out[r.fuente] = { lat: r.lat, lon: r.lon, tipo: r.tipo, dir: r.dir };
        }
        return json(out);
      }

      if (request.method === "POST") {
        const key = request.headers.get("X-Admin-Key");
        if (!env.ADMIN_KEY || key !== env.ADMIN_KEY) {
          return json({ error: "No autorizado" }, 401);
        }

        let body;
        try {
          body = await request.json();
        } catch {
          return json({ error: "Body inválido, se esperaba JSON" }, 400);
        }
        const { fuente, lat, lon, tipo, dir } = body || {};
        if (!fuente || typeof fuente !== "string") {
          return json({ error: "Falta 'fuente'" }, 400);
        }
        if (lat !== null && typeof lat !== "number") {
          return json({ error: "'lat' debe ser number o null" }, 400);
        }
        if (lon !== null && typeof lon !== "number") {
          return json({ error: "'lon' debe ser number o null" }, 400);
        }

        await env.DB.prepare(
          `INSERT INTO coords (fuente, lat, lon, tipo, dir, actualizado_en)
           VALUES (?, ?, ?, ?, ?, datetime('now'))
           ON CONFLICT(fuente) DO UPDATE SET
             lat = excluded.lat,
             lon = excluded.lon,
             tipo = excluded.tipo,
             dir = excluded.dir,
             actualizado_en = excluded.actualizado_en`
        )
          .bind(fuente, lat ?? null, lon ?? null, tipo ?? null, dir ?? null)
          .run();

        return json({ ok: true });
      }

      return json({ error: "Método no permitido" }, 405);
    } catch (err) {
      return json({ error: err.message }, 500);
    }
  },
};