// Copia el paquete de datos del pipeline a public/datos/<version>/ después de validar
// cada archivo contra schema/. La web solo lee datos que cumplen el contrato.
//
// Origen: METABO_DATOS (carpeta data/<version>/) o, si no existe, la versión más
// reciente de ../data/. Uso: npm run datos (lo corren `dev` y `build`).
import { cp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../..");
const outRoot = path.resolve(here, "../public/datos");

// Carpeta del paquete -> esquema que valida sus archivos.
const SCHEMA_BY_FOLDER = {
  vias: "via",
  compuestos: "compuesto",
  reacciones: "reaccion",
  enzimas: "enzima",
  organismos: "organismo",
  cobertura: "cobertura",
  mapas: "mapa",
  referencias: "referencia",
};

async function sourceDir() {
  if (process.env.METABO_DATOS) return path.resolve(process.env.METABO_DATOS);
  const base = path.join(repo, "data");
  const versions = (await readdir(base).catch(() => [])).filter((v) => /^\d{4}\.\d{2}$/.test(v));
  if (versions.length === 0) {
    throw new Error(
      "No hay paquete de datos. Genéralo con `cd pipeline && uv run metabo exportar` " +
        "o indica su carpeta con METABO_DATOS.",
    );
  }
  return path.join(base, versions.sort().at(-1));
}

async function jsonFiles(dir) {
  const entries = await readdir(dir, { recursive: true, withFileTypes: true });
  return entries
    .filter((e) => e.isFile() && e.name.endsWith(".json"))
    .map((e) => path.join(e.parentPath, e.name));
}

const ajv = new Ajv2020({ allErrors: true, strict: false });
for (const file of await readdir(path.join(repo, "schema"))) {
  if (file.endsWith(".schema.json")) {
    ajv.addSchema(JSON.parse(await readFile(path.join(repo, "schema", file), "utf8")));
  }
}
const schemaId = (name) => `https://luvelasquez.github.io/metaboatlas/schema/${name}.schema.json`;

const src = await sourceDir();
const manifest = JSON.parse(await readFile(path.join(src, "manifest.json"), "utf8"));
const errors = [];
if (!ajv.validate(schemaId("manifiesto"), manifest)) errors.push(`manifest.json: ${ajv.errorsText()}`);
let count = 0;
for (const file of await jsonFiles(src)) {
  const relative = path.relative(src, file);
  const folder = relative.split(path.sep)[0];
  const schema = SCHEMA_BY_FOLDER[folder];
  if (relative === "manifest.json") continue;
  if (!schema) {
    errors.push(`${relative}: carpeta sin esquema`);
    continue;
  }
  const data = JSON.parse(await readFile(file, "utf8"));
  if (!ajv.validate(schemaId(schema), data)) errors.push(`${relative}: ${ajv.errorsText()}`);
  count += 1;
}
if (errors.length > 0) {
  console.error(`El paquete de ${src} no cumple schema/:\n  ${errors.join("\n  ")}`);
  process.exit(1);
}

const version = manifest.version_datos;
await rm(outRoot, { recursive: true, force: true });
await mkdir(outRoot, { recursive: true });
await cp(src, path.join(outRoot, version), { recursive: true });
await writeFile(path.join(outRoot, "version.json"), JSON.stringify({ version }) + "\n");
console.log(`Paquete ${version}: ${count} archivos validados y copiados a public/datos/${version}/`);
