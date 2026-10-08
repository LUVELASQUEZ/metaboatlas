// Genera los tipos TypeScript del paquete de datos desde schema/ (el contrato único
// entre el pipeline y la web). Uso: npm run tipos. No edites lib/tipos/ a mano.
import { rm, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { compileFromFile } from "json-schema-to-typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const schemaDir = path.resolve(here, "../../schema");
const outDir = path.resolve(here, "../lib/tipos");

// Esquemas de archivos que la web lee del paquete de datos.
const SCHEMAS = ["via", "compuesto", "reaccion", "enzima", "organismo", "cobertura", "mapa", "manifiesto", "referencia"];

const banner = "// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.\n";

await rm(outDir, { recursive: true, force: true });
await mkdir(outDir, { recursive: true });
for (const name of SCHEMAS) {
  const ts = await compileFromFile(path.join(schemaDir, `${name}.schema.json`), {
    cwd: schemaDir,
    bannerComment: banner,
    additionalProperties: false,
    style: { singleQuote: false, printWidth: 100 },
  });
  await writeFile(path.join(outDir, `${name}.ts`), ts);
}
console.log(`${SCHEMAS.length} tipos generados en lib/tipos/`);
