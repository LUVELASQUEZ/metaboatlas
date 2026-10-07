// Revisión de accesibilidad (WCAG 2.2 AA) con axe-core sobre el sitio construido.
// Uso: npm run build && npm run a11y. Sirve out/ bajo el basePath y revisa cada
// página en modo claro y oscuro. METABO_CHROMIUM permite usar un Chromium ya instalado.
import { createReadStream, existsSync, readFileSync, statSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(here, "../out");
const base = process.env.METABO_BASE_PATH ?? "/metaboatlas";
const axe = readFileSync(path.resolve(here, "../node_modules/axe-core/axe.min.js"), "utf8");

const PAGINAS = [
  "/",
  "/fuentes/",
  "/glosario/",
  "/glosario/nad/",
  "/via/glucolisis/",
  "/via/glucolisis/?org=511145&paso=p03",
  "/via/glucolisis/?org=9606&compuesto=CHEBI:59776",
  "/via/glucolisis/?nivel=intermedio&org=559292",
  "/via/glucolisis/?nivel=avanzado&paso=p10",
];
const TIPOS = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
};

if (!existsSync(out)) {
  console.error("Falta out/: corre `npm run build` primero.");
  process.exit(1);
}
const servidor = http
  .createServer((req, res) => {
    const ruta = decodeURIComponent(new URL(req.url ?? "/", "http://x").pathname);
    let archivo = path.join(out, ruta.slice(base.length));
    if (existsSync(archivo) && statSync(archivo).isDirectory()) archivo = path.join(archivo, "index.html");
    if (!ruta.startsWith(base) || !existsSync(archivo)) {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, { "content-type": TIPOS[path.extname(archivo)] ?? "application/octet-stream" });
    createReadStream(archivo).pipe(res);
  })
  .listen(0);
const { port } = servidor.address();

const navegador = await chromium.launch(
  process.env.METABO_CHROMIUM ? { executablePath: process.env.METABO_CHROMIUM } : {},
);
let fallas = 0;
for (const esquema of ["light", "dark"]) {
  const pagina = await navegador.newPage({ colorScheme: esquema });
  for (const ruta of PAGINAS) {
    const respuesta = await pagina.goto(`http://localhost:${port}${base}${ruta}`, {
      waitUntil: "networkidle",
    });
    if (!respuesta?.ok()) {
      console.error(`✗ ${esquema} ${ruta}: HTTP ${respuesta?.status()}`);
      fallas += 1;
      continue;
    }
    await pagina.addScriptTag({ content: axe });
    const resultado = await pagina.evaluate(() =>
      window.axe.run(document, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
      }),
    );
    for (const v of resultado.violations) {
      fallas += 1;
      console.error(`✗ ${esquema} ${ruta}: ${v.id} (${v.impact}) ${v.help}`);
      for (const n of v.nodes.slice(0, 5)) console.error(`    ${n.target.join(" ")}`);
    }
    if (resultado.violations.length === 0) console.log(`✓ ${esquema} ${ruta}`);
  }
  await pagina.close();
}
await navegador.close();
servidor.close();
process.exit(fallas > 0 ? 1 : 0);
