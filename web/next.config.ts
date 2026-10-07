import type { NextConfig } from "next";

// El sitio se publica en GitHub Pages bajo https://<usuario>.github.io/metaboatlas/.
// METABO_BASE_PATH="" sirve el sitio en la raíz (por ejemplo, con otro dominio).
const basePath = process.env.METABO_BASE_PATH ?? "/metaboatlas";

const config: NextConfig = {
  output: "export",
  basePath,
  assetPrefix: basePath || undefined,
  trailingSlash: true,
  images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
};

export default config;
