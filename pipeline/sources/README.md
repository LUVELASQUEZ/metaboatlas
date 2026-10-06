# pipeline/sources/

Un módulo de extracción por base de datos (`rhea.py`, `uniprot.py`, …). Solo descargas oficiales y API documentadas de fuentes registradas en `sources.yaml`; User-Agent con correo de contacto, reintentos con espera exponencial y registro SHA-256 en `manifest.json`.
