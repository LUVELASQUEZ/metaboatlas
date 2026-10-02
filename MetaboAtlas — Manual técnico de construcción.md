# MetaboAtlas — Manual técnico de construcción

Oct 1, 2026 · @Luisa Fernanda Velasquez Zapata

## Resumen ejecutivo y uso del manual

MetaboAtlas (nombre provisional) es una aplicación web pública, gratuita y de código abierto que muestra mapas metabólicos de referencia, calcula su presencia en cientos de organismos y los explica en español por niveles, citando siempre la base de datos de origen. Replica la lógica de conexiones de KEGG, pero se construye solo con datos de licencia abierta y deja a KEGG y BioCyc como destinos de enlace.

Decisiones de base que este manual ya asume:

- **Datos**: solo fuentes con licencia abierta verificada (CC0, CC BY 4.0, dominio público). KEGG, BioCyc/MetaCyc, HMDB y similares quedan como enlaces externos.
- **Modelo**: vía de referencia única + cobertura calculada por organismo a partir de enzimas anotadas en UniProt y reacciones de Rhea.
- **Arquitectura**: sitio estático pre-generado. Un pipeline en Python descarga y procesa los datos en GitHub Actions; la web en Next.js se publica sin servidor propio. Costo de operación: cero.
- **Diferencial**: mapas propios dibujados con criterio didáctico, contenido en tres niveles, comparador entre organismos y citación automática.

Cómo leer el manual: las secciones siguen el orden de construcción (licencias → datos → modelo → cálculo → diseño → software → calidad → despliegue → fases). Los puntos marcados **Por verificar** requieren confirmar una licencia o un límite técnico antes de implementar, porque estas condiciones cambian con el tiempo.

## 1. Visión, público y alcance

La app debe permitir que un estudiante de primer semestre entienda una vía en cinco minutos y que un tesista obtenga, en la misma pantalla, los identificadores y referencias que necesita para su trabajo.

### Público y necesidades

| Perfil | Carreras | Qué busca | Qué le damos |
| --- | --- | --- | --- |
| Estudiante que aprende | Bacteriología, microbiología, biología, nutrición | Entender qué hace una vía y por qué importa | Nivel básico, recorrido paso a paso, glosario |
| Estudiante de investigación o tesis | Bioquímica, biotecnología, microbiología | Datos verificables, IDs, presencia en su organismo | Nivel avanzado, comparador, exportación, citas |
| Docente | Todas | Material para clase y para dejar tareas | Enlaces compartibles con estado, rutas de aprendizaje |

### Alcance del MVP

- 10 vías del metabolismo central: glucólisis, gluconeogénesis, ciclo de Krebs, fosforilación oxidativa, pentosas fosfato, fermentación láctica, fermentación alcohólica, β-oxidación, síntesis de ácidos grasos y ciclo de la urea.
- Cobertura precalculada para unos 50 organismos de referencia (modelos procariotas y eucariotas más organismos de interés clínico e industrial), con cálculo en vivo para cualquier otro en una fase posterior.
- Fichas de compuesto, reacción, enzima y organismo.
- Buscador, niveles didácticos, citación y página de fuentes.

### Fuera de alcance del MVP

- Cuentas de usuario, comentarios o foros.
- Simulación de flujos metabólicos (FBA) y modelos a escala genómica.
- Datos de pacientes o uso diagnóstico. La app es educativa y debe decirlo en su aviso legal.

### Principios de diseño

1. **Trazabilidad total**: cada dato visible lleva su fuente, su identificador, la versión de la base y la fecha de descarga.
2. **Solo datos abiertos**: si una fuente no tiene licencia abierta verificada, solo se enlaza.
3. **Didáctica progresiva**: lo simple primero; el detalle se revela a pedido, nunca se oculta.
4. **Español primero**: nombres, explicaciones e interfaz en español, con el nombre en inglés y el ID siempre visibles para conectar con la literatura.
5. **Costo cero y robustez**: nada que dependa de un servidor que se apague o de un plan pago.
6. **Accesible**: legible en celular, navegable con teclado y apta para daltonismo.

## 2. Política de licencias

Regla de oro: ningún dato entra al pipeline si su fuente no tiene una fila en esta matriz con la licencia verificada en su página oficial y la fecha de verificación. La matriz vive en el repositorio como `sources.yaml` y la app la muestra en la página Fuentes.

### Fuentes que se pueden redistribuir

| Fuente | Licencia | Qué tomamos | Condición |
| --- | --- | --- | --- |
| Reactome | CC BY 4.0 | Jerarquía de vías, reacciones, participantes, especies inferidas, textos descriptivos, referencias bibliográficas | Atribución e indicar cambios (traducciones) |
| WikiPathways | CC0 | Vías por especie con coordenadas de dibujo (GPML) y referencias cruzadas | Ninguna; se cita por buena práctica |
| Rhea | CC BY 4.0 | Reacciones balanceadas, dirección, participantes ChEBI, número EC | Atribución |
| ChEBI | CC BY 4.0 | Compuestos: nombre, fórmula, carga, masa, SMILES, InChI, sinónimos, ontología de roles | Atribución |
| UniProtKB | CC BY 4.0 | Enzimas por organismo: EC, reacciones Rhea, genes, cofactores, GO, nivel de revisión | Atribución |
| ENZYME (Expasy) | CC BY 4.0 | Nomenclatura EC oficial, nombres aceptados, jerarquía de clases | Atribución |
| Gene Ontology | CC BY 4.0 | Procesos biológicos y funciones moleculares | Atribución |
| NCBI Taxonomy | Dominio público | Linaje, rangos, nombres científicos y comunes | Citar la fuente |
| Wikidata | CC0 | Nombres en español de compuestos, enzimas y taxones; enlaces a Wikipedia en español | Ninguna |
| BRENDA | CC BY 4.0 ([licencia](https://brenda-enzymes.de/license.php)) | Cinética (Km, kcat), inhibidores, pH y temperatura óptimos (fase 3) | Atribución; aceptar la licencia antes de descargar |
| Europe PMC | Metadatos abiertos | Título, autores, revista y DOI de artículos citados | Citar la fuente |
| Escher (software) | MIT | Referencia de notación y, opcionalmente, editor de diseños | Conservar aviso MIT |

BRENDA declara que el uso de sus datos está bajo CC BY 4.0 y pide citar su publicación más reciente. Se confirma así la decisión de incluirla en la fase 3.

### Por verificar antes de integrar

- **PubChem**: en general es de dominio público, pero algunos datos de depositantes tienen condiciones propias. Usar solo CID, propiedades calculadas y enlaces.
- **BiGG Models y sus mapas Escher**: revisar los términos actuales del sitio y de cada modelo.
- **MetaNetX**: confirmar la licencia de los archivos MNXref, útiles para reconciliar identificadores.
- **Human-GEM y Yeast-GEM**: modelos en GitHub; confirmar la licencia en cada repositorio.

### Solo enlace (no se copia ningún dato)

| Fuente | Motivo | Cómo se usa |
| --- | --- | --- |
| KEGG | Uso académico gratuito solo en su web; prestar un servicio con KEGG requiere licencia de pago ([términos](https://www.kegg.jp/kegg/legal.html)) | Enlace profundo a la vía, a la vía del organismo, al compuesto y a la enzima |
| BioCyc / MetaCyc | La mayoría de bases de organismos requieren suscripción | Enlace a la vía y a la reacción |
| HMDB, SMPDB, VMH | Licencias con condiciones de uso | Enlace a la ficha del metabolito o vía humana |

### Excluido

- Copiar, recortar o redibujar a mano imágenes de mapas de KEGG o BioCyc.
- Extraer datos de cualquier sitio por scraping en lugar de usar sus descargas o API oficiales.
- Usar la API de KEGG desde el pipeline o desde el navegador.

### Licencias propias del proyecto

- Código: MIT.
- Contenido didáctico y datos compilados: CC BY 4.0, compatible con las fuentes CC BY y CC0 siempre que se conserve la atribución de cada una.

## 3. Catálogo de fuentes: qué extraer de cada base

Se prefieren siempre las descargas masivas versionadas sobre las API, porque son reproducibles y no castigan los servidores de las fuentes. Las API se usan solo para consultas puntuales o para el modo en vivo. Todas las rutas deben confirmarse al implementar, porque las bases reorganizan sus servidores.

### Reactome — columna vertebral de vías

- **Extraer**: jerarquía de vías (bajo "Metabolism"), reacciones con entradas, salidas, catalizadores y compartimentos, especies (humano curado y unas 15 especies inferidas por ortología), resúmenes en inglés (summation), referencias PubMed y relaciones entre vías.
- **Acceso**: descargas en `reactome.org/download/current/` (ReactomePathways.txt, ReactomePathwaysRelation.txt, UniProt2Reactome.txt, ChEBI2Reactome.txt) y Content Service REST en `reactome.org/ContentService` para el detalle de cada evento.
- **Uso**: definir los pasos de las vías de referencia, evidencia adicional para eucariotas y fuente de los textos que se traducen y adaptan.

### WikiPathways — dibujos de partida

- **Extraer**: archivos GPML por especie con coordenadas de nodos y aristas, nodos con referencias a ChEBI, Ensembl o UniProt, autores y fecha de revisión.
- **Acceso**: volcados de datos por especie y endpoint SPARQL (`sparql.wikipathways.org`).
- **Uso**: punto de partida para los diseños de mapas (al ser CC0 se pueden adaptar libremente) y validación cruzada de pasos.

### Rhea — reacciones

- **Extraer**: ID de reacción maestra y sus tres variantes de dirección (izquierda a derecha, derecha a izquierda, bidireccional), ecuación, participantes ChEBI con estequiometría, número EC asociado, indicador de transporte y referencias a MetaCyc, KEGG y Reactome.
- **Acceso**: archivos TSV en `ftp.expasy.org/databases/rhea/tsv/` (rhea-directions.tsv, rhea2ec.tsv, rhea2uniprot) y SPARQL en `sparql.rhea-db.org`.
- **Uso**: unidad básica de cada paso del mapa y puente entre enzima y compuesto. Rhea representa las especies químicas predominantes a pH 7,3, lo que explica por qué se muestra "piruvato" y no "ácido pirúvico".

### ChEBI — compuestos

- **Extraer**: nombre, definición, fórmula, carga, masa monoisotópica, SMILES, InChI e InChIKey, sinónimos, relaciones de ontología (rol "cofactor", "metabolito de E. coli", relación ácido/base conjugada) y referencias cruzadas (KEGG COMPOUND, HMDB, PubChem).
- **Acceso**: archivos de `ftp.ebi.ac.uk/pub/databases/chebi/` y ontología OWL. **Por verificar**: ChEBI ha cambiado formatos de descarga recientemente.
- **Uso**: ficha de compuesto, dibujo de la estructura en el navegador y clasificación de colores por tipo de molécula.

### UniProtKB — enzimas por organismo

- **Extraer**: accesión, nombre de proteína y gen, organismo (taxon ID), número EC, actividad catalítica con ID Rhea, cofactores, vía (comentario pathway), términos GO, si es revisada (Swiss-Prot) o automática (TrEMBL), puntaje de anotación y referencias cruzadas (KEGG gene, Reactome, PDB, AlphaFold).
- **Acceso**: REST `rest.uniprot.org/uniprotkb/stream` con consulta por proteoma y campos seleccionados (`accession, protein_name, gene_names, organism_id, ec, rhea, cc_catalytic_activity, cc_cofactor, go_p, reviewed, annotation_score, xref_kegg`), y `rest.uniprot.org/proteomes` para la lista de proteomas de referencia.
- **Uso**: núcleo del cálculo de cobertura por organismo (sección 5). La referencia cruzada a KEGG gene trae el código de organismo de KEGG (por ejemplo "eco"), que permite construir los enlaces profundos sin consultar KEGG.

### ENZYME (Expasy) — nomenclatura EC

- **Extraer**: número EC, nombre aceptado, nombres alternativos, reacción, cofactores, estado (vigente, transferido, eliminado) y jerarquía de clases.
- **Acceso**: `ftp.expasy.org/databases/enzyme/` (enzyme.dat y enzclass.txt).
- **Uso**: ficha de enzima y navegación por las siete clases EC.

### NCBI Taxonomy — árbol de organismos

- **Extraer**: taxon ID, nombre científico, nombres comunes, rango y linaje completo.
- **Acceso**: `ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/`.
- **Uso**: selector de organismos agrupado por dominio, filo y género; perfil de organismo.

### Wikidata — el puente al español

- **Extraer**: etiquetas y descripciones en español de compuestos (propiedad ChEBI ID, P683), enzimas (número EC, P591) y taxones (NCBI taxon ID, P685), más el enlace al artículo de Wikipedia en español.
- **Acceso**: SPARQL en `query.wikidata.org/sparql`, consultas por lotes de 200 a 500 IDs.
- **Uso**: nombres en español por defecto; cuando falte una etiqueta, se marca para traducción manual.

### Gene Ontology

- **Extraer**: términos de proceso biológico (por ejemplo, "glycolytic process") con su jerarquía.
- **Acceso**: `go-basic.obo` desde el repositorio OBO.
- **Uso**: enlazar enzimas con procesos y detectar enzimas candidatas cuando falta la anotación Rhea.

### Europe PMC — bibliografía

- **Extraer**: título, autores, revista, año, DOI y si es de acceso abierto, a partir de los PMID que traen Reactome y UniProt.
- **Acceso**: REST `ebi.ac.uk/europepmc/webservices/rest/search`.
- **Uso**: lista de lecturas recomendadas por vía, con preferencia por artículos de acceso abierto.

### BRENDA — cinética (fase 3)

- **Extraer**: Km, kcat, Ki, pH y temperatura óptimos por enzima y organismo, con su referencia.
- **Acceso**: archivo de descarga tras aceptar la licencia (requiere registro).
- **Uso**: nivel avanzado de la ficha de enzima.

### PubChem — apoyo químico

- **Extraer**: CID y propiedades calculadas (peso molecular, XLogP) por InChIKey.
- **Acceso**: PUG REST en `pubchem.ncbi.nlm.nih.gov/rest/pug/`.
- **Uso**: enlace externo y datos fisicoquímicos complementarios.

### Enlaces profundos (solo enlace)

| Destino | Patrón de enlace | De dónde sale el ID |
| --- | --- | --- |
| KEGG vía de referencia | `kegg.jp/pathway/map00010` | Curado a mano en cada vía (son pocas) |
| KEGG vía de un organismo | `kegg.jp/pathway/eco00010` | Código de organismo desde UniProt + número de mapa |
| KEGG compuesto | `kegg.jp/entry/C00022` | Referencia cruzada de ChEBI |
| KEGG enzima | `kegg.jp/entry/2.7.1.1` | Número EC |
| MetaCyc reacción y vía | Página de MetaCyc | Referencia cruzada de Rhea; vías curadas a mano |
| HMDB metabolito | Página de HMDB | Referencia cruzada de ChEBI |

## 4. Modelo de información

La información se organiza en una red, igual que en KEGG: cualquier entidad lleva a las demás. Una vía se compone de pasos; cada paso es una reacción catalizada por una actividad enzimática; cada organismo "tiene" o "no tiene" esa actividad según sus proteínas anotadas.

### Jerarquía de navegación

1. **Categoría** (Metabolismo de carbohidratos, de lípidos, de aminoácidos, energético, de nucleótidos, de cofactores y vitaminas). Clasificación propia en español.
   1. **Vía de referencia** (glucólisis). Independiente del organismo.
      1. **Módulo**: bloque funcional con sentido didáctico (fase preparatoria y fase de beneficio de la glucólisis).
         1. **Paso**: una posición en el mapa (fosforilación de la glucosa).
            1. **Reacción** (ID Rhea) con sus **compuestos** (ID ChEBI) y su **actividad enzimática** (número EC).
               1. **Proteínas** concretas de cada **organismo** (accesión UniProt), que determinan la cobertura.

Además de la jerarquía, existen conexiones transversales: un compuesto aparece en varias vías (el piruvato conecta glucólisis, Krebs y fermentaciones), y esas conexiones forman el **mapa general**.

### Entidades y campos principales

| Entidad | ID interno | Campos clave | Referencias cruzadas |
| --- | --- | --- | --- |
| Categoría | `cat:carbohidratos` | Nombre, descripción, orden, icono | GO (proceso) |
| Vía | `via:glucolisis` | Nombres es/en, categoría, módulos, pasos, compartimento, vías conectadas, variantes, versión, estado editorial | Reactome, WikiPathways, GO, KEGG map, MetaCyc |
| Módulo | `via:glucolisis/m1` | Nombre, pasos, resumen didáctico | — |
| Paso | `via:glucolisis/p01` | Orden, reacciones válidas (alternativas), EC, si es espontáneo, si es punto de regulación, si consume o produce ATP/NADH | Rhea, EC |
| Reacción | `RHEA:16109` | Ecuación, participantes y estequiometría, dirección, reversibilidad, compartimento, ΔG si hay fuente | Rhea, MetaCyc, Reactome, KEGG |
| Compuesto | `CHEBI:15361` | Nombres es/en, fórmula, carga, masa, SMILES, InChIKey, clase, es cofactor | KEGG, HMDB, PubChem, Wikidata |
| Enzima (actividad) | `EC:2.7.1.1` | Nombre aceptado, alternativos, clase EC, cofactores | ENZYME, BRENDA, KEGG |
| Proteína | `UNIPROT:P0A6T1` | Gen, organismo, EC, Rhea, revisada sí/no, puntaje de anotación | KEGG gene, PDB, AlphaFold |
| Organismo | `taxon:511145` | Nombre científico, cepa, linaje, dominio, gram, proteoma de referencia, interés (modelo, clínico, industrial) | NCBI Taxonomy, código KEGG |
| Cobertura | `via:glucolisis@taxon:511145` | Estado por paso, porcentaje, clase de cobertura, fecha de cálculo | — |
| Fuente | `src:rhea` | Nombre, licencia, versión, fecha de descarga, URL, cita recomendada | — |

### Identificadores

- Los IDs externos se usan tal cual en formato CURIE (`CHEBI:15361`, `RHEA:16109`, `EC:2.7.1.1`). Así son estables y reconocibles por los investigadores.
- Las entidades propias (categoría, vía, módulo, paso) usan slugs en español sin tildes. Una vez publicados, nunca cambian; si una vía se renombra, el slug antiguo redirige.
- Toda referencia cruzada se guarda como par `(fuente, id)` y se convierte en enlace con plantillas de URL centralizadas en `sources.yaml`.

### Ejemplo de una vía en JSON

```json
{
  "id": "via:glucolisis",
  "nombre": { "es": "Glucólisis", "en": "Glycolysis" },
  "categoria": "cat:carbohidratos",
  "compartimento": ["citosol"],
  "modulos": [
    { "id": "m1", "nombre": "Fase preparatoria", "pasos": ["p01", "p02", "p03", "p04", "p05"] },
    { "id": "m2", "nombre": "Fase de beneficio", "pasos": ["p06", "p07", "p08", "p09", "p10"] }
  ],
  "pasos": [
    {
      "id": "p01",
      "titulo": "Fosforilación de la glucosa",
      "reacciones": ["RHEA:..."],
      "ec": ["EC:2.7.1.1", "EC:2.7.1.2"],
      "regulacion": true,
      "energia": { "ATP": -1 }
    }
  ],
  "conecta_con": ["via:pentosas-fosfato", "via:krebs", "via:fermentacion-lactica"],
  "xrefs": { "kegg_map": "map00010", "reactome": "R-HSA-...", "wikipathways": "WP..." },
  "version": "2026.10",
  "estado_editorial": "validado"
}
```

Los IDs de Rhea y Reactome se dejan con puntos suspensivos a propósito: se completan durante la curaduría de cada vía, nunca de memoria.

## 5. Vía de referencia + organismos: cálculo de cobertura

Cada vía se dibuja una sola vez; el organismo seleccionado solo cambia el color de cada paso según la evidencia de que ese organismo tiene la enzima. Es la misma idea del coloreado de KEGG, calculada con UniProt y Rhea.

### Algoritmo por paso

Para un paso P y un organismo O:

1. Si P es espontáneo (no requiere enzima), se marca **espontáneo** y siempre cuenta como presente.
2. Si existe una proteína **revisada** (Swiss-Prot) del proteoma de O anotada con alguna reacción Rhea de P, el paso es **presente, evidencia alta**.
3. Si no, pero existe una proteína **no revisada** (TrEMBL, anotación automática por reglas) con esa reacción Rhea, es **presente, evidencia media**.
4. Si no, pero existe una proteína con alguno de los números EC de P (sin Rhea), es **probable, evidencia baja**.
5. Si no hay nada, el paso es **sin anotación**. Nunca se dice "ausente": la falta de anotación no prueba que la función no exista.

El orden de búsqueda prioriza Rhea sobre EC porque un número EC puede agrupar reacciones distintas, mientras que un ID Rhea describe una reacción exacta.

### Cobertura de la vía

```latex
\text{Cobertura}(V, O) = \frac{\text{pasos presentes o espontáneos}}{\text{pasos totales de } V} \times 100
```

| Clase | Regla | Mensaje al usuario |
| --- | --- | --- |
| Completa | 100 % de pasos con evidencia alta o media | "Este organismo tiene todas las enzimas de la vía." |
| Casi completa | Al menos 80 % | "Faltan pasos sin anotar; pueden existir enzimas no caracterizadas." |
| Parcial | Entre 30 % y 80 % | "El organismo tiene parte de la vía; puede usar una variante." |
| No detectada | Menos de 30 % | "No encontramos evidencia de esta vía en este organismo." |

Los umbrales son configurables en `pipeline/config.yaml` y deben ajustarse con los casos de prueba de la sección 14.

### Variantes de una vía

Algunos organismos llegan al mismo resultado por otro camino: la vía de Entner-Doudoroff en lugar de la glucólisis clásica, o el ciclo del glioxilato como atajo del ciclo de Krebs. Se modelan como vías propias enlazadas con la relación `variante_de`, para que el estudiante vea "tu organismo no usa la glucólisis clásica completa, pero sí Entner-Doudoroff".

### Isoenzimas y complejos

- **Isoenzimas**: varias proteínas que catalizan el mismo paso (hexocinasa y glucocinasa). Basta una para marcar presencia; la ficha las lista todas.
- **Complejos multiproteicos**: el complejo piruvato deshidrogenasa necesita varias subunidades. En el MVP se exige al menos una subunidad anotada y se muestra la advertencia "complejo: verificar subunidades". En fases posteriores se puede exigir el conjunto completo.

### Qué organismos se precalculan

- **MVP**: lista curada de unos 50 organismos con proteoma de referencia en UniProt, en tres grupos: modelos (por ejemplo *E. coli* K-12, *B. subtilis* 168, *S. cerevisiae*, humano, ratón, *Arabidopsis*), de interés clínico (*Staphylococcus aureus*, *Pseudomonas aeruginosa*, *Mycobacterium tuberculosis*, *Candida albicans*, entre otros) y de interés industrial o alimentario (*Lactobacillus*, *Corynebacterium glutamicum*, *Aspergillus niger*, entre otros). La lista final la decide el equipo y vive en `pipeline/organismos.yaml`.
- **Fase 2, modo en vivo**: para cualquier otro taxón, el navegador consulta la API de UniProt (que admite consultas directas desde el navegador), aplica el mismo algoritmo en JavaScript y muestra el resultado con la etiqueta "calculado ahora".

El algoritmo debe existir una sola vez como especificación y dos implementaciones (Python en el pipeline y TypeScript en el modo en vivo) que pasan el mismo conjunto de pruebas.

### Formato de salida

```json
{
  "via": "via:glucolisis",
  "taxon": "taxon:511145",
  "cobertura": 100,
  "clase": "completa",
  "pasos": {
    "p01": { "estado": "alta", "proteinas": ["UNIPROT:..."] },
    "p02": { "estado": "alta", "proteinas": ["UNIPROT:P0A6T1"] }
  },
  "calculado": "2026-10-01",
  "fuentes": { "uniprot": "2026_04", "rhea": "..." }
}
```

Con 50 organismos y 10 vías son 500 archivos pequeños, del orden de pocos kilobytes cada uno.

### Advertencia didáctica obligatoria

Cada vista de cobertura muestra un aviso breve: "La cobertura se calcula a partir de anotaciones en bases de datos. Un paso sin anotación puede deberse a una enzima aún no caracterizada." Enseñar esta limitación es parte del valor educativo.

## 6. Pipeline de datos (ETL)

Un único comando (`uv run metabo build`) reconstruye todos los datos publicados desde cero, de forma reproducible. Corre en GitHub Actions una vez al mes o a demanda, y su resultado es un paquete versionado de archivos JSON que consume la web.

### Etapas

1. **Extraer**: un módulo por fuente (`pipeline/sources/rhea.py`, `uniprot.py`, etc.) descarga los archivos a `raw/<fuente>/<versión>/`, guarda la suma de verificación SHA-256 y registra versión, fecha y URL en el manifiesto. Respeta los límites de cada servicio, usa un User-Agent con correo de contacto y reintentos con espera exponencial.
2. **Cargar**: los archivos crudos se cargan en una base DuckDB local (`staging.duckdb`), una tabla por archivo, sin transformar.
3. **Normalizar**: se unifican identificadores (CURIE), se resuelven reacciones Rhea a su ID maestro, se reconcilian compuestos equivalentes (formas ácido/base) usando la ontología de ChEBI y, si se confirma su licencia, MetaNetX.
4. **Integrar curaduría**: se leen las definiciones de vías escritas a mano (`curation/vias/*.yaml`) con sus pasos, módulos y referencias. Esta es la única parte que no sale de una base de datos y es la que da identidad al proyecto.
5. **Enriquecer**: nombres en español desde Wikidata, bibliografía desde Europe PMC, linaje desde NCBI Taxonomy.
6. **Calcular**: cobertura de cada vía en cada organismo (sección 5) e índice inverso compuesto → vías y enzima → vías.
7. **Validar**: esquemas (pydantic y JSON Schema), integridad referencial (todo ID citado existe), reglas biológicas de prueba (sección 14) e informe de diferencias contra la versión anterior. Si algo falla, no se publica.
8. **Exportar**: JSON por entidad, índice de búsqueda, `manifest.json` de procedencia y `CHANGELOG` de datos.
9. **Publicar**: el paquete se sube como asset de un GitHub Release etiquetado `data-2026.10` y dispara la construcción del sitio.

### Estructura del paquete de datos

```
data/2026.10/
  manifest.json            # fuentes, versiones, fechas, licencias, checksums
  vias/glucolisis.json     # definición, pasos y referencias
  mapas/glucolisis.json    # coordenadas del dibujo
  cobertura/glucolisis/511145.json
  compuestos/CHEBI_15361.json
  reacciones/RHEA_xxxxx.json
  enzimas/EC_2.7.1.1.json
  organismos/511145.json
  indices/busqueda.json
  indices/compuesto-a-vias.json
```

### Volumen esperado en el MVP

Solo se exportan las entidades que tocan las vías incluidas: del orden de 150 a 300 compuestos, 150 a 250 reacciones, 100 a 200 actividades EC, 50 organismos y 500 archivos de cobertura. El paquete completo debería quedar por debajo de 50 MB. La descarga de UniProt se limita a los proteomas de la lista y a los campos necesarios, no a la base completa.

### Calendario de actualización

| Fuente | Frecuencia de publicación aproximada | Qué hace el pipeline |
| --- | --- | --- |
| UniProt | Cada \~8 semanas | Recalcula cobertura |
| Reactome | Trimestral | Actualiza referencias y textos fuente |
| Rhea, ChEBI | Frecuente | Actualiza fichas |
| Wikidata | Continua | Refresca nombres en español |

El job mensual detecta si alguna fuente cambió de versión; si ninguna cambió, no publica nada nuevo.

### Herramientas

Python 3.12, gestor `uv`, `httpx` + `tenacity` para descargas, `duckdb` y `polars` para transformar, `pydantic` para modelos, `pytest` para pruebas, `pronto` u `obonet` para ontologías y `SPARQLWrapper` para Wikidata y Rhea.

## 7. Diseño de los mapas metabólicos

Los mapas se dibujan a mano una vez por vía, con coordenadas guardadas en JSON, y se renderizan con Cytoscape.js. Un diseño curado es más didáctico que uno automático: la glucólisis debe "verse" como en los libros, de arriba hacia abajo, con la fase preparatoria separada de la de beneficio.

### Notación visual

Inspirada en el estándar SBGN (Process Description), simplificada para estudiantes:

| Elemento | Forma | Detalle |
| --- | --- | --- |
| Metabolito principal | Círculo con etiqueta en español | Color según su clase química; tamaño mayor si es punto de conexión (piruvato, acetil-CoA) |
| Cofactor o metabolito "moneda" | Círculo pequeño a un lado de la flecha | ATP, ADP, NAD+, NADH, CoA, H2O, CO2, Pi. Se duplica en cada reacción para no enredar el mapa y se puede ocultar |
| Reacción | Flecha | Punta simple si es irreversible en condiciones fisiológicas; doble punta si es reversible |
| Enzima | Rótulo redondeado sobre la flecha | Nombre corto y número EC; color según la evidencia del organismo seleccionado |
| Paso regulado | Rótulo con borde grueso y un icono de "válvula" | Marca los puntos de control (hexocinasa, fosfofructocinasa, piruvato cinasa) |
| Paso espontáneo | Flecha punteada sin rótulo | — |
| Compartimento | Región de fondo con esquinas redondeadas | Citosol, matriz mitocondrial, membrana, periplasma |
| Conexión con otra vía | Rótulo tipo "portal" en el borde | Lleva al otro mapa, igual que los rótulos de vías en KEGG |

### Colores por evidencia

Paleta apta para daltonismo (Okabe-Ito), siempre acompañada de un patrón o icono, nunca solo color:

| Estado | Color | Refuerzo no cromático |
| --- | --- | --- |
| Evidencia alta | Azul #0072B2 | Borde continuo |
| Evidencia media | Verde azulado #009E73 | Borde continuo fino |
| Evidencia baja | Naranja #E69F00 | Borde discontinuo |
| Sin anotación | Gris #BDBDBD | Rótulo atenuado con signo de interrogación |
| Sin organismo seleccionado | Tono neutro de la marca | — |

### Cómo se producen los diseños

1. Se parte del GPML de WikiPathways (CC0) o se dibuja desde cero.
2. Se ajusta en un editor propio sencillo: una página interna `/editor` que permite arrastrar nodos sobre la cuadrícula y exportar el JSON. Alternativa: el editor de Escher (MIT) con un conversor.
3. El JSON guarda solo posiciones y rutas de flechas por ID de paso y compuesto; los datos se toman del paquete de datos. Así el dibujo no se desactualiza cuando cambian los datos.
4. Para vías sin diseño curado (fases futuras), se genera un diseño automático por capas con ELK.js y se etiqueta "diseño automático".

### Interacciones

- **Navegar**: zoom con rueda o pellizco, arrastrar, botón "ajustar a pantalla" y minimapa en escritorio.
- **Explorar**: pasar el cursor muestra un resumen; hacer clic abre el panel lateral con la ficha completa del compuesto, la reacción o la enzima.
- **Seleccionar organismo**: el selector recolorea los pasos sin recargar la página y actualiza la barra de cobertura.
- **Recorrido paso a paso**: un reproductor con anterior, siguiente y reproducir resalta cada paso en orden, muestra un texto corto y anima el flujo de la molécula a lo largo de la flecha.
- **Contador de energía**: durante el recorrido suma ATP, NADH y FADH2 consumidos y producidos, para cerrar con el balance neto de la vía.
- **Resaltar ruta**: elegir dos metabolitos y resaltar el camino más corto entre ellos.
- **Capas**: mostrar u ocultar cofactores, números EC, compartimentos y conexiones.
- **Exportar**: PNG y SVG del mapa con la leyenda y la línea de atribución incluidas automáticamente.
- **Vista de tabla**: equivalente accesible del mapa, con todos los pasos en orden; sirve para lectores de pantalla y para copiar datos.

### Mapa general

Una vista "metro" donde cada vía es una línea y los metabolitos compartidos son estaciones de transbordo (glucosa-6-fosfato, piruvato, acetil-CoA, oxalacetato). Con un organismo seleccionado, las líneas no detectadas se atenúan. Es la puerta de entrada visual al resto del atlas y el equivalente didáctico del mapa global de KEGG.

### Versión móvil

En celular el mapa ocupa toda la pantalla, la ficha aparece como una hoja inferior deslizable y el reproductor paso a paso se convierte en la forma principal de recorrer la vía, porque en pantalla pequeña un mapa completo es difícil de leer.

## 8. Sistema de diseño: gentil y académico

La estética de referencia es la de un buen libro de texto moderno: fondo cálido tipo papel, tipografía con serifa para los títulos, mucho espacio en blanco y color usado solo para transmitir significado. Nada de efectos llamativos que compitan con el mapa.

### Paleta (tokens)

| Token | Modo claro | Modo oscuro | Uso |
| --- | --- | --- | --- |
| `--fondo` | #FAF8F4 | #15191C | Fondo general |
| `--superficie` | #FFFFFF | #1E2428 | Tarjetas, paneles |
| `--tinta` | #1F2A33 | #E8E6E1 | Texto principal |
| `--tinta-suave` | #5B6770 | #A9B1B7 | Texto secundario |
| `--primario` | #1F6F78 | #5FB3BC | Botones, enlaces, foco |
| `--acento` | #B7791F | #E0A84E | Resaltados didácticos, paso activo |
| `--borde` | #E4DFD6 | #2E363B | Divisiones |

Todo par texto/fondo debe cumplir contraste WCAG AA (4,5:1 en texto normal). Los valores son una propuesta inicial; se ajustan con pruebas reales.

### Colores por clase de molécula

Suaves y diferenciables, con forma o icono de apoyo: carbohidratos (ámbar claro), lípidos (amarillo arena), aminoácidos (verde salvia), nucleótidos (lavanda), cofactores y moneda energética (gris azulado), iones y gases (gris claro). La clase se deriva de la ontología de ChEBI.

### Tipografía

- **Títulos**: Source Serif 4 (serifa académica, licencia OFL).
- **Texto e interfaz**: Atkinson Hyperlegible o Inter (alta legibilidad, licencia OFL).
- **IDs y fórmulas**: JetBrains Mono (OFL).
- Escala: 14, 16, 18, 22, 28 y 36 px; texto de lectura en 17–18 px con interlineado 1,6 y ancho máximo de 70 caracteres.
- Fórmulas químicas con subíndices reales (C₆H₁₂O₆), nunca "C6H12O6".

### Forma y espacio

Escala de espaciado de 4 px (4, 8, 12, 16, 24, 32, 48), esquinas redondeadas de 10 px en tarjetas y 6 px en controles, sombras muy suaves y líneas finas. Iconos de línea de Lucide (licencia ISC).

### Tono de voz

Cercano y respetuoso, en tú, sin infantilizar. Frases cortas, término técnico seguido de su explicación la primera vez ("la fosforilación, es decir, la adición de un grupo fosfato"). Mensajes de error que dicen qué pasó y qué hacer.

### Componentes base

| Componente | Función |
| --- | --- |
| `Buscador` | Campo con autocompletado agrupado por tipo (vía, compuesto, enzima, organismo) |
| `TarjetaVia` | Nombre, categoría, miniatura del mapa, cobertura si hay organismo |
| `SelectorOrganismo` | Búsqueda por nombre, agrupado por dominio y grupo de interés |
| `LienzoMapa` | Contenedor de Cytoscape.js con controles de zoom, capas y exportación |
| `PanelFicha` | Panel lateral (hoja inferior en móvil) con la ficha de la entidad |
| `SelectorNivel` | Básico, intermedio, avanzado; recuerda la elección del usuario |
| `ReproductorPasos` | Recorrido paso a paso con contador de energía |
| `BarraCobertura` | Porcentaje y desglose por evidencia |
| `LeyendaEvidencia` | Explica colores y patrones |
| `CajaFuentes` | Fuentes, IDs, versiones y botón de citar |
| `TerminoGlosario` | Palabra subrayada que abre su definición |
| `MatrizComparacion` | Pasos por organismos con estados de evidencia |
| `InsigniaEditorial` | Borrador, revisado o validado, con nombre del revisor |

Los componentes se construyen sobre primitivas accesibles (Radix UI) y se documentan en Storybook para mantener la consistencia.

## 9. Pantallas y flujos de usuario

Toda la aplicación cabe en 12 tipos de pantalla, y el estado de cada una (vía, organismo, nivel, paso activo) vive en la URL para que cualquier vista se pueda compartir o dejar como tarea.

### Mapa de rutas

| Ruta | Pantalla | Contenido principal |
| --- | --- | --- |
| `/` | Inicio | Buscador grande, mapa general en miniatura, rutas de aprendizaje, accesos por carrera |
| `/explorar` | Explorar | Categorías → vías, con filtros por compartimento y organismo |
| `/via/[slug]?org=&nivel=&paso=` | Vía | Mapa, selector de organismo, nivel, reproductor, panel de ficha, cobertura, fuentes |
| `/mapa-general?org=` | Mapa general | Vista "metro" de todas las vías |
| `/comparar?via=&orgs=` | Comparador | Matriz pasos × organismos y mapas lado a lado |
| `/compuesto/[chebi]` | Compuesto | Estructura, nombres, fórmula, vías donde participa, reacciones, enlaces externos |
| `/reaccion/[rhea]` | Reacción | Ecuación, dirección, enzimas, organismos con la enzima |
| `/enzima/[ec]` | Enzima | Nombre, clase EC, reacción, cofactores, proteínas por organismo, cinética (fase 3) |
| `/organismo/[taxon]` | Organismo | Linaje, rasgos, vías con su cobertura, enlaces a UniProt, NCBI y KEGG |
| `/glosario` y `/glosario/[termino]` | Glosario | Términos con definición, ejemplo y vías relacionadas |
| `/aprender/[ruta]` | Ruta de aprendizaje | Secuencia de vías con objetivos y autoevaluación |
| `/fuentes`, `/como-citar`, `/acerca` | Institucional | Matriz de licencias, versiones de datos, cita del proyecto, equipo, aviso legal |

### Pantalla de vía en detalle

- **Encabezado**: nombre en español y en inglés, categoría, compartimento, insignia editorial y botón "Citar".
- **Barra de controles**: selector de organismo, selector de nivel, capas, exportar.
- **Centro**: el mapa (o la vista de tabla).
- **Panel derecho**: por defecto muestra el resumen de la vía según el nivel; al hacer clic en un elemento, muestra su ficha. En móvil es una hoja inferior.
- **Debajo del mapa**: explicación por niveles, balance energético, regulación, relevancia por carrera, vías conectadas, lecturas recomendadas y caja de fuentes.

### Flujos clave

**Estudiante que estudia para un parcial**

1. Busca "Krebs" en el inicio y entra a la vía en nivel básico.
2. Presiona reproducir y recorre los 8 pasos con el contador de energía.
3. Toca "succinato" y lee su ficha; toca un término subrayado y ve su definición.
4. Al final responde 3 preguntas de autoevaluación.

**Estudiante de microbiología que compara organismos**

1. Entra a glucólisis, elige *E. coli* y ve cobertura completa.
2. Cambia a un organismo con cobertura parcial y lee la sugerencia de variante (Entner-Doudoroff).
3. Abre el comparador con ambos organismos y exporta la matriz en CSV para su informe.

**Tesista que busca una enzima**

1. Busca "2.7.1.11" o "fosfofructocinasa".
2. En la ficha de la enzima ve en qué organismos hay proteínas revisadas, con accesiones UniProt.
3. Copia la cita en APA de Rhea y UniProt y sigue el enlace a KEGG para profundizar.

**Docente que prepara una clase**

1. Abre la β-oxidación en nivel intermedio con humano seleccionado y el paso 3 activo.
2. Copia el enlace (que conserva ese estado) y lo comparte con su grupo.
3. Descarga el mapa en SVG con la atribución incluida para su presentación.

### Estados que toda pantalla debe resolver

Cargando (esqueletos grises, nunca pantalla en blanco), vacío ("no encontramos resultados; prueba con el nombre en inglés o el número EC"), error de red en modo en vivo ("no pudimos consultar UniProt; intenta de nuevo") y sin conexión si se activa la PWA.

## 10. Capa didáctica

El contenido didáctico es lo que convierte los datos en una herramienta de aprendizaje, y es también el trabajo más largo: cada vía necesita entre 1.500 y 3.000 palabras revisadas. Se escribe una vez por vía de referencia, no por organismo.

### Tres niveles por vía

| Nivel | Pregunta que responde | Contenido |
| --- | --- | --- |
| Básico | ¿Qué hace y para qué sirve? | Resumen de 3 a 5 frases, analogía, entrada y salida principales, dónde ocurre, por qué importa |
| Intermedio | ¿Cómo funciona? | Los pasos con sus enzimas, balance energético, puntos de regulación, conexiones con otras vías |
| Avanzado | ¿Qué dicen los datos? | Mecanismos, regulación alostérica y genética, variantes entre organismos, termodinámica, IDs, lecturas primarias |

El nivel cambia el texto y también el mapa: en básico se ocultan los números EC y los cofactores; en avanzado se muestran todos.

### Plantilla de contenido de una vía

Cada vía es un archivo `content/vias/<slug>.mdx` con metadatos y estas secciones:

1. Resumen por nivel.
2. Paso a paso: un texto corto por paso, usado por el reproductor.
3. Balance energético (tabla de ATP, NADH, FADH2 consumidos y producidos).
4. Regulación.
5. Relevancia por carrera: microbiología (fermentaciones, identificación bioquímica), bacteriología clínica, nutrición (ayuno, ejercicio, dieta), biotecnología (producción industrial), bioquímica.
6. Errores frecuentes de los estudiantes ("el NADH no es energía por sí mismo").
7. Preguntas de autoevaluación con respuesta explicada.
8. Referencias: cada afirmación no trivial apunta a una fuente de la sección 11.

### Glosario

Archivos `content/glosario/<termino>.mdx` con definición breve, definición ampliada, ejemplo y vías relacionadas. Un componente detecta la primera aparición de cada término en un texto y la convierte en `TerminoGlosario`.

### Rutas de aprendizaje

Secuencias guiadas de vías con objetivos, por ejemplo: "Del azúcar a la energía" (glucólisis → Krebs → fosforilación oxidativa), "Metabolismo microbiano y fermentaciones" y "Ayuno y alimentación" (glucógeno → gluconeogénesis → β-oxidación).

### Autoevaluación

Preguntas en JSON dentro del repositorio: opción múltiple, ordenar pasos (arrastrar), identificar la enzima en el mapa y calcular un balance. Se corrigen en el navegador y no se guardan resultados en el MVP, por lo que no hay datos personales.

### Reglas de redacción

- Nombres en español según la nomenclatura bioquímica de uso académico, con el nombre en inglés entre paréntesis la primera vez.
- Usar la forma iónica a pH fisiológico (piruvato, lactato, citrato) y explicar en el glosario por qué.
- Frases de menos de 25 palabras; un concepto por párrafo.
- Cada cifra (rendimiento de ATP, ΔG) con su fuente, porque los valores varían entre libros.

### Flujo editorial y validación

1. **Borrador**: se escribe (a mano o con apoyo de IA a partir de los textos de Reactome y las fuentes primarias). Todo texto generado con IA se marca así hasta su revisión.
2. **Revisado**: un revisor con formación en el área revisa el pull request en GitHub con una lista de verificación (exactitud, referencias, claridad, nivel).
3. **Validado**: un segundo revisor, idealmente docente universitario, aprueba. La insignia de la pantalla muestra el estado y los nombres de quienes revisaron.

Las traducciones y adaptaciones de textos de Reactome deben indicar "adaptado y traducido de Reactome" con enlace, como exige CC BY 4.0.

## 11. Referenciación y citación

Cada dato que ve el usuario puede rastrearse hasta su base de origen, con versión y fecha, y citarse en un clic. Esto cumple las licencias CC BY y, sobre todo, enseña al estudiante a citar bien.

### Tres niveles de referencia

1. **Por dato**: cada valor de una ficha lleva una pequeña insignia de fuente (por ejemplo "Rhea") que al tocarla muestra el ID, la versión y el enlace directo.
2. **Por página**: la `CajaFuentes` al final de cada página lista todas las bases usadas, con licencia, versión, fecha de descarga y el botón "Citar".
3. **Global**: la página `/fuentes` muestra la matriz de licencias completa y el `manifest.json` de la versión de datos vigente.

### Registro central de fuentes

`sources.yaml` es la única fuente de verdad para todo lo anterior:

```yaml
rhea:
  nombre: Rhea
  url: https://www.rhea-db.org
  licencia: CC BY 4.0
  licencia_url: <página oficial de licencia>
  verificada: 2026-10-01
  plantillas:
    reaccion: https://www.rhea-db.org/rhea/{id}
  cita_recomendada: <copiada textualmente de la página "How to cite" de Rhea>
  doi_cita: <DOI del artículo recomendado>
```

La cita recomendada de cada base se copia de su página oficial de citación y se revisa en cada actualización anual; nunca se escribe de memoria.

### Generador de citas

- Formatos: APA 7, Vancouver (frecuente en ciencias de la salud) y exportación BibTeX y RIS para Zotero o Mendeley.
- Qué se cita al pulsar "Citar" en una vía: la publicación recomendada de cada base usada en esa página, la entrada concreta (por ejemplo, la reacción Rhea con fecha de consulta) y MetaboAtlas con su versión.
- Implementación: `citation-js` (licencia MIT) para formatear a partir de metadatos CSL-JSON; los metadatos de artículos se obtienen de Europe PMC o por DOI en el pipeline, no en el navegador.

### Citar MetaboAtlas

- Cada versión publicada en GitHub se archiva automáticamente en Zenodo, que asigna un DOI gratuito.
- Un archivo `CITATION.cff` en el repositorio hace que GitHub muestre el botón "Cite this repository".
- La página `/como-citar` explica cuándo citar la app y cuándo citar directamente la base de datos original. En trabajos académicos se debe preferir la fuente primaria.

### Atribución en exportaciones

Toda imagen, CSV o SVG exportado incluye una línea de atribución automática, por ejemplo: "Datos: Rhea, ChEBI y UniProt (CC BY 4.0), versiones 2026\_04. Mapa: MetaboAtlas v1.0 (CC BY 4.0)."

### Lecturas recomendadas

Por vía se listan de 3 a 8 artículos tomados de las referencias de Reactome y UniProt, priorizando revisiones y artículos de acceso abierto, con enlace a Europe PMC y DOI.

## 12. Arquitectura de software

La arquitectura es "JAMstack con datos precompilados": un pipeline en Python genera un paquete de datos, Next.js lo convierte en un sitio estático y un CDN gratuito lo sirve. No hay servidor ni base de datos en producción; el navegador solo lee archivos JSON y, en el modo en vivo, consulta UniProt directamente.

&#91;embedded content: arquitectura de MetaboAtlas · de las fuentes al navegador\]

Las líneas discontinuas son conexiones opcionales desde el navegador: la consulta en vivo a UniProt y los enlaces de salida a bases con licencia restringida.

### Capas

1. **Fuentes externas**: descargas y API de Reactome, WikiPathways, Rhea, ChEBI, UniProt, ENZYME, NCBI Taxonomy, Wikidata, Europe PMC.
2. **Pipeline** (GitHub Actions, mensual): extrae, normaliza en DuckDB, integra curaduría, calcula cobertura, valida y exporta.
3. **Paquete de datos** versionado (GitHub Release `data-AAAA.MM`).
4. **Contenido** (MDX en el repositorio): textos didácticos, glosario, rutas, preguntas.
5. **Construcción del sitio** (Next.js con exportación estática): genera una página HTML por vía, compuesto, enzima, reacción y organismo, más el índice de búsqueda.
6. **Hosting** (CDN gratuito): sirve HTML, JS y JSON.
7. **Navegador**: React + Cytoscape.js; lee el JSON de mapas y coberturas bajo demanda; en modo en vivo consulta la API de UniProt.

### Stack

| Capa | Tecnología | Por qué |
| --- | --- | --- |
| Lenguaje web | TypeScript | Tipos compartidos con los esquemas de datos |
| Framework | Next.js (App Router, `output: 'export'`) | Páginas estáticas con buen SEO, rutas dinámicas pre-generadas |
| Estilos | Tailwind CSS + variables CSS de la sección 8 | Consistencia y modo oscuro sencillo |
| Componentes accesibles | Radix UI | Menús, diálogos y pestañas accesibles por defecto |
| Mapas | Cytoscape.js (MIT) | Rendimiento, zoom, estilos y eventos maduros |
| Diseño automático | ELK.js (EPL) | Diseño por capas para vías sin dibujo curado |
| Estructuras químicas | SmilesDrawer (MIT) o RDKit.js (BSD) | Dibujo 2D desde SMILES en el navegador |
| Contenido | MDX con Velite o Contentlayer2 | Textos en archivos versionados, validados por esquema |
| Búsqueda | MiniSearch para entidades + Pagefind para textos | Búsqueda sin servidor |
| Estado en URL | `nuqs` | Organismo, nivel y paso compartibles |
| Validación | Zod (generado desde JSON Schema) | Mismo contrato que el pipeline |
| Citas | citation-js | APA, Vancouver, BibTeX, RIS |
| Gráficos | Recharts o Observable Plot | Barras de cobertura y comparaciones |
| Pipeline | Python 3.12, uv, DuckDB, Polars, pydantic | Reproducible y rápido en una máquina gratuita de CI |
| Pruebas | pytest, Vitest, Playwright, axe-core | Datos, lógica, flujos y accesibilidad |

Las versiones exactas se fijan al iniciar el repositorio (**Por verificar**: compatibilidad de Next.js estático con las librerías elegidas).

### Estructura del repositorio (monorepo)

```
metaboatlas/
├─ pipeline/                 # Python
│  ├─ sources/               # un módulo por base de datos
│  ├─ transform/             # normalización e integración
│  ├─ coverage/              # algoritmo de cobertura
│  ├─ export/                # JSON, índices, manifiesto
│  ├─ config.yaml            # umbrales y parámetros
│  ├─ organismos.yaml        # lista curada de organismos
│  └─ tests/
├─ curation/
│  ├─ vias/*.yaml            # definición de pasos y módulos por vía
│  └─ mapas/*.json           # coordenadas del dibujo por vía
├─ content/                  # MDX en español
│  ├─ vias/  glosario/  aprender/  preguntas/
├─ schema/                   # JSON Schema: contrato pipeline ↔ web
├─ web/                      # Next.js
│  ├─ app/                   # rutas de la sección 9
│  ├─ components/            # componentes de la sección 8
│  ├─ lib/                   # carga de datos, cobertura en vivo, citas
│  └─ tests/
├─ sources.yaml              # registro de fuentes y licencias
├─ CITATION.cff  LICENSE  LICENSE-content  CONTRIBUTING.md
└─ .github/workflows/        # pipeline.yml, web.yml, checks.yml
```

### Contrato entre pipeline y web

La carpeta `schema/` define cada archivo del paquete de datos con JSON Schema. El pipeline valida su salida contra esos esquemas y la web genera sus tipos TypeScript a partir de ellos. Si alguien cambia un campo, ambos lados fallan en las pruebas antes de llegar a producción.

### Carga de datos en la web

- En construcción: se leen las vías, compuestos, enzimas y organismos para generar las páginas estáticas con su texto (bueno para buscadores).
- En el navegador: el mapa y la cobertura del organismo elegido se descargan solo cuando se necesitan, con caché del navegador.
- Modo en vivo (fase 2): `lib/cobertura-vivo.ts` consulta UniProt por taxón y Rhea de la vía, aplica el algoritmo y guarda el resultado en memoria de la sesión.

## 13. Búsqueda, rendimiento, accesibilidad, SEO e idioma

### Búsqueda

- **Qué se indexa**: vías, compuestos, enzimas, reacciones, organismos y términos del glosario, con nombre en español, nombre en inglés, sinónimos de ChEBI y ENZYME, IDs (CHEBI, RHEA, EC, accesión UniProt, taxon) y fórmula.
- **Cómo**: índice MiniSearch precompilado en el pipeline (unos cientos de KB para el MVP), cargado al primer uso del buscador; Pagefind indexa los textos largos de las páginas.
- **Reglas**: insensible a tildes y mayúsculas ("glucolisis" encuentra "glucólisis"), tolerancia a errores de un carácter, reconocimiento de patrones (si el texto parece un EC, un CHEBI o una fórmula, se prioriza ese tipo) y resultados agrupados por tipo.
- **Sin resultados**: sugerir el término en inglés, el número EC o el glosario.

### Rendimiento

| Métrica | Objetivo |
| --- | --- |
| Lighthouse rendimiento (móvil) | ≥ 90 |
| Largest Contentful Paint | < 2,5 s en 4G |
| JavaScript inicial | < 200 KB comprimido |
| Mapa de una vía (JSON) | < 100 KB |

Técnicas: Cytoscape.js y el dibujo de estructuras se cargan solo en las páginas que los usan; los JSON se sirven comprimidos y con caché larga porque su ruta incluye la versión de datos; las fuentes tipográficas se autoalojan con subconjunto latino.

### Accesibilidad (WCAG 2.2 AA)

- Contraste mínimo verificado en ambos modos.
- Color nunca como único portador de significado (patrones e iconos en la evidencia).
- Navegación completa con teclado: el mapa permite moverse entre nodos con Tab y flechas, y Enter abre la ficha.
- Vista de tabla como equivalente textual del mapa para lectores de pantalla.
- `prefers-reduced-motion` desactiva las animaciones del recorrido.
- Textos alternativos en estructuras químicas (nombre y fórmula).
- Pruebas automáticas con axe-core en cada pull request y una revisión manual con lector de pantalla por versión.

### SEO y descubrimiento

- Una página estática por entidad con título y descripción en español ("Glucólisis: pasos, enzimas y balance energético").
- Datos estructurados schema.org: `LearningResource` en vías, `Dataset` en la página de datos, `ChemicalSubstance` en compuestos.
- `sitemap.xml` y `robots.txt` generados en la construcción; URLs limpias y estables.
- Etiquetas Open Graph con imagen del mapa para que los enlaces compartidos en WhatsApp o redes muestren una vista previa.

### Idioma

- Español como idioma por defecto y único en el MVP, con la estructura de internacionalización preparada (`next-intl`, textos de interfaz en archivos de mensajes) para agregar inglés o portugués más adelante.
- Los nombres de entidades se guardan siempre en ambos idiomas (es/en) desde el pipeline.

### PWA (fase 4)

Instalable en el celular y con las vías visitadas disponibles sin conexión, útil para estudiantes con datos móviles limitados.

## 14. Calidad, pruebas y validación científica

Una app educativa que enseña algo incorrecto hace daño, así que la calidad se controla en tres frentes: los datos, el software y el contenido. Ningún cambio llega a producción sin pasar las pruebas automáticas y, si toca contenido, sin revisión humana.

### Pruebas de datos (pipeline)

- **Esquema**: cada archivo exportado cumple su JSON Schema.
- **Integridad referencial**: todo ID citado en una vía existe en el paquete; ningún paso queda sin reacción o sin EC.
- **Balance**: las reacciones de Rhea están balanceadas por definición; se verifica que la curaduría no haya asociado una reacción equivocada a un paso comparando los compuestos del mapa con los participantes Rhea.
- **Diferencias entre versiones**: informe automático de qué coberturas cambiaron y por qué (por ejemplo "glucólisis en *X*: 80 % → 100 % por nueva anotación en UniProt"). Un cambio grande inesperado bloquea la publicación hasta revisión.

### Verdades biológicas (pruebas de regresión)

Casos que el algoritmo de cobertura debe reproducir siempre. Se escriben como pruebas con su referencia bibliográfica. Ejemplos a confirmar durante la curaduría:

| Caso | Resultado esperado |
| --- | --- |
| Glucólisis en *E. coli* K-12 | Completa |
| Ciclo del glioxilato en *E. coli* K-12 | Completa (tiene isocitrato liasa y malato sintasa) |
| Ciclo del glioxilato en humano | No detectada |
| Ciclo de la urea completo en *E. coli* | No detectada |
| Fermentación alcohólica en *S. cerevisiae* | Completa |
| Ciclo de Krebs en humano | Completa |

Cuando una prueba falla, se investiga si el error está en el algoritmo, en la curaduría o en un cambio real de la anotación.

### Pruebas de software (web)

- **Unitarias** (Vitest): algoritmo de cobertura en TypeScript con los mismos casos que el de Python, formateo de citas, normalización de búsqueda.
- **De componentes** (Storybook + pruebas de interacción): selector de organismo, reproductor, panel de ficha.
- **De extremo a extremo** (Playwright): los cuatro flujos de la sección 9, en escritorio y en móvil.
- **Visuales**: capturas de cada mapa comparadas contra la versión anterior para detectar dibujos rotos.
- **Accesibilidad**: axe-core en cada página principal.
- **Rendimiento**: Lighthouse CI con los umbrales de la sección 13.

### Validación del contenido

- Flujo borrador → revisado → validado de la sección 10, con lista de verificación en la plantilla del pull request.
- Formulario "Reportar un error científico" en cada página, que crea un issue en GitHub con la URL y el estado de la vista ya incluidos.
- Revisión anual completa de cada vía validada.

### Control de versiones y trazabilidad

- Versionado semántico para la app (`v1.2.0`) y por fecha para los datos (`2026.10`); la interfaz muestra ambas en el pie de página.
- `CHANGELOG.md` de la app y changelog de datos generado por el pipeline.
- Todo cambio entra por pull request con revisión; la rama principal está protegida y exige que pasen todas las verificaciones.

## 15. Despliegue, operación, costos y gobernanza

Todo el proyecto opera en planes gratuitos: GitHub para código, CI y paquetes de datos, y GitHub Pages para el sitio. El único gasto opcional es un dominio propio.

### Servicios y costo

| Necesidad | Servicio recomendado | Alternativa | Costo |
| --- | --- | --- | --- |
| Repositorio público | GitHub | GitLab | 0 |
| CI y pipeline mensual | GitHub Actions (gratuito en repositorios públicos) | — | 0 |
| Paquetes de datos | GitHub Releases | Zenodo | 0 |
| Hosting del sitio | GitHub Pages (decidido) | Cloudflare Pages, Netlify | 0 |
| Analítica respetuosa de la privacidad | Cloudflare Web Analytics (sin cookies) | GoatCounter | 0 |
| DOI del proyecto | Zenodo | — | 0 |
| Dominio propio | Subdominio gratuito del hosting | Dominio .org o .co | 0 o costo anual bajo |

Se descarta Vercel Hobby como principal porque su plan gratuito está pensado para uso personal no comercial, y conviene no depender de esa condición si en el futuro se suma una institución. **Por verificar**: límites vigentes de cada plan gratuito (número de archivos por despliegue, tamaño máximo por archivo, minutos de CI).

Implicaciones de usar GitHub Pages: el sitio queda en `usuario.github.io/metaboatlas`, por lo que Next.js necesita configurar `basePath` y `assetPrefix` con el nombre del repositorio, y agregar un archivo `.nojekyll` en la salida. El despliegue se hace con la acción oficial de Pages desde GitHub Actions. GitHub Pages no genera vistas previas por pull request; para revisar desde el iPad, se publica una rama de prueba o se revisan las capturas de Playwright que deja el CI. **Por verificar**: límites vigentes de tamaño del sitio y de ancho de banda.

### Flujos de CI/CD

1. `checks.yml`: en cada pull request ejecuta lint, pruebas del pipeline, pruebas web, accesibilidad y Lighthouse; publica una vista previa del sitio con su propia URL.
2. `pipeline.yml`: mensual (cron) o manual; reconstruye los datos, valida, publica el Release `data-AAAA.MM` y abre un pull request que actualiza la versión de datos usada por la web, con el informe de diferencias en la descripción.
3. `web.yml`: al fusionar en la rama principal, construye el sitio estático con la versión de datos fijada y lo despliega.

Así ningún dato nuevo llega al público sin que alguien revise el informe de diferencias.

### Operación

- **Monitoreo**: verificación de disponibilidad gratuita (por ejemplo UptimeRobot) y alertas de fallo de los workflows por correo.
- **Errores del navegador**: opcionalmente Sentry en su plan gratuito, sin datos personales.
- **Privacidad**: sin cuentas, sin cookies de seguimiento y sin almacenar datos personales en el MVP; aviso de privacidad breve igualmente publicado.
- **Mantenimiento**: revisión mensual del pipeline, revisión trimestral de dependencias (Dependabot) y revisión anual de licencias y citas en `sources.yaml`.

### Gobernanza del proyecto abierto

- Licencias: MIT para el código; CC BY 4.0 para contenido y datos compilados.
- Archivos: `README` en español e inglés, `CONTRIBUTING.md` (cómo proponer una vía, cómo revisar contenido), `CODE_OF_CONDUCT.md`, plantillas de issues (error de software, error científico, propuesta de vía).
- Roles: mantenedora del proyecto, revisores científicos por área y colaboradores de código.
- Hoja de ruta pública en GitHub Projects.
- Aviso legal: herramienta educativa, sin uso diagnóstico ni clínico; los datos provienen de terceros y pueden contener errores.

### Si el proyecto se vincula a una universidad

Una alianza permitiría sumar revisores docentes, darle visibilidad institucional y, si la institución lo gestiona, obtener la licencia de proveedor de servicios académicos de KEGG para integrar sus datos como fuente adicional.

## 16. Hoja de ruta, riesgos y checklist de arranque

El orden propuesto es construir primero una sola vía de punta a punta (glucólisis), porque obliga a resolver todas las piezas una vez; después escalar es repetir. Las duraciones suponen una persona a tiempo parcial con apoyo de IA para el código y deben ajustarse al ritmo real.

### Fases

1. **Fase 0 — Fundamentos (3 a 4 semanas)**: repositorio, licencias verificadas en `sources.yaml`, JSON Schema, pipeline mínimo (Rhea, ChEBI, UniProt, ENZYME, NCBI Taxonomy), sistema de diseño base y la glucólisis completa con 4 organismos.
   - Criterio para avanzar: la glucólisis se ve, se colorea por organismo, cada dato muestra su fuente y las pruebas de verdades biológicas pasan.
2. **Fase 1 — MVP público (6 a 10 semanas)**: las 10 vías, unos 50 organismos, fichas de compuesto, reacción, enzima y organismo, buscador, niveles, reproductor, citación, página de fuentes, despliegue y DOI.
   - Criterio: al menos 2 revisores validan el contenido de cada vía, Lighthouse ≥ 90 y accesibilidad sin errores críticos.
3. **Fase 2 — Comparar y conectar**: comparador de organismos, mapa general, variantes de vías, modo en vivo para cualquier organismo y exportaciones CSV/SBML.
4. **Fase 3 — Profundidad**: metabolismo de aminoácidos, nucleótidos, cofactores y vitaminas; cinética de BRENDA; rutas de aprendizaje y autoevaluación completas.
5. **Fase 4 — Comunidad**: guía para que docentes propongan vías, versión en inglés, PWA sin conexión y posibles alianzas institucionales.

### Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Una fuente cambia su licencia | Alto | Revisión anual de `sources.yaml`; el pipeline permite apagar una fuente sin romper la app |
| Anotación incompleta da falsos "sin anotación" | Medio | Niveles de evidencia, aviso didáctico, vías variantes |
| Errores científicos en el contenido | Alto | Flujo de revisión en dos pasos y botón de reporte |
| El contenido toma más tiempo del previsto | Alto | Publicar con pocas vías bien hechas antes que muchas a medias |
| Cambian formatos o URLs de descarga | Medio | Un módulo por fuente y pruebas que detectan el cambio antes de publicar |
| Límites de los planes gratuitos | Bajo | Paquete de datos pequeño y hosting intercambiable |
| Proyecto dependiente de una sola persona | Medio | Documentación, código abierto y colaboradores desde la fase 1 |

### Checklist de arranque

- [ ] Elegir el nombre definitivo y verificar que el dominio y el nombre de usuario de GitHub estén libres
- [ ] Crear el repositorio público con licencias, README y CONTRIBUTING
- [ ] Verificar y registrar en `sources.yaml` la licencia y la cita recomendada de cada fuente de la sección 2
- [ ] Confirmar la lista de 50 organismos y sus proteomas de referencia
- [ ] Escribir el JSON Schema de vía, paso, compuesto, reacción, enzima, organismo y cobertura
- [ ] Curar `curation/vias/glucolisis.yaml` con sus Rhea, EC y módulos
- [ ] Implementar los extractores de Rhea, ChEBI, UniProt, ENZYME y NCBI Taxonomy
- [ ] Implementar el algoritmo de cobertura con sus pruebas de verdades biológicas
- [ ] Dibujar el mapa de la glucólisis y probarlo en Cytoscape.js
- [ ] Crear el proyecto Next.js con el sistema de diseño y la página de vía
- [ ] Escribir el contenido de la glucólisis en tres niveles y someterlo a revisión
- [ ] Configurar los workflows de CI y el primer despliegue de prueba
- [ ] Conseguir al menos dos revisores científicos (docentes o profesionales del área)

### Fuentes consultadas para este manual

- [KEGG — Copyright and Disclaimer](https://www.kegg.jp/kegg/legal.html)
- [KEGG API — restricción de uso](https://www.genome.jp/kegg/rest/)
- [BRENDA — License & disclaimer](https://brenda-enzymes.de/license.php)

El resto de licencias y rutas proviene de conocimiento general a la fecha y está marcado para verificación donde corresponde.
