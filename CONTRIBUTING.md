# Cómo contribuir a MetaboAtlas

Gracias por tu interés. MetaboAtlas es un proyecto educativo: su valor depende de que lo que enseña sea correcto y verificable. Esta guía explica cómo proponer cambios de código, de datos y de contenido.

Antes de empezar, lee el manual técnico en [`docs/MANUAL.md`](docs/MANUAL.md).

## Reglas que nunca se rompen

1. **Solo datos abiertos.** Solo se descargan y redistribuyen datos de fuentes registradas en [`sources.yaml`](sources.yaml) con licencia verificada (CC0, CC BY 4.0 o dominio público). Si una fuente no está en `sources.yaml`, no se usa.
2. **KEGG, BioCyc/MetaCyc, HMDB, SMPDB y VMH son solo enlaces.** No se llama a sus API, no se descargan sus archivos y no se copian ni se redibujan sus mapas.
3. **Nada de scraping.** Solo descargas oficiales y API documentadas, respetando sus límites de uso.
4. **Trazabilidad total.** Todo dato exportado lleva fuente, identificador, versión de la base y fecha de descarga.
5. **No se inventan identificadores** (Rhea, ChEBI, EC, UniProt, taxones, Reactome). Si un ID no sale de los datos descargados, el campo queda pendiente con un `TODO`.
6. **No se escriben citas de memoria.** Las citas recomendadas se copian de la página oficial "How to cite" de cada base.
7. **"Sin anotación" no es "ausente".** Nunca se afirma que un organismo carece de una vía.
8. **Costo cero.** Nada de servicios pagos ni servidores propios.

## Flujo de trabajo

1. Abre un *issue* que describa el cambio, o comenta en uno existente.
2. Crea una rama desde `main` con un nombre descriptivo (por ejemplo, `via-glucolisis` o `pipeline-rhea`).
3. Haz cambios pequeños y enfocados, con mensajes de commit en español.
4. Abre un *pull request* que explique:
   - **Qué se hizo.**
   - **Cómo probarlo** (comandos y resultados esperados).
   - **Qué quedó pendiente.**
5. Todo cambio necesita revisión y que pasen las verificaciones automáticas antes de fusionarse.

### Definición de terminado

Un cambio está listo cuando las pruebas pasan, los datos exportados validan contra [`schema/`](schema/), el linter no reporta errores, la documentación afectada está actualizada y el *pull request* explica cómo verificar el resultado.

## Convenciones

- **Idioma:** interfaz, contenido, documentación y mensajes de commit en español. Los identificadores de código (funciones, variables, archivos de código) van en inglés. Las claves de los JSON de datos siguen el manual y van en español (`nombre`, `pasos`, `cobertura`).
- **IDs externos** en formato CURIE: `CHEBI:15361`, `RHEA:16109`, `EC:2.7.1.1`, `UNIPROT:P0A6T1`, `taxon:511145`. En nombres de archivo, `:` se reemplaza por `_` (`CHEBI_15361.json`).
- **IDs propios** como slugs en español, sin tildes ni mayúsculas (`via:glucolisis`, `cat:carbohidratos`). Una vez publicados no cambian.
- **Accesibilidad:** todo componente nuevo cumple WCAG 2.2 AA y nunca usa el color como único portador de significado.

## Proponer una fuente de datos

1. Verifica la licencia en la página oficial de la fuente.
2. Agrega o actualiza su entrada en `sources.yaml` con la URL de la licencia, la fecha de verificación y la cita recomendada copiada textualmente de su página de citación.
3. Explica en el *pull request* dónde verificaste cada dato.

Si la licencia no es CC0, CC BY 4.0 o dominio público, la fuente solo puede usarse como enlace.

## Proponer una vía

1. Abre un *issue* con el nombre de la vía, su categoría y por qué es útil para el público del proyecto.
2. Crea `curation/vias/<slug>.yaml` con sus módulos, pasos, reacciones Rhea y números EC, obtenidos de datos descargados (Rhea, UniProt, Reactome) y nunca de memoria.
3. Agrega el dibujo en `curation/mapas/<slug>.json`, partiendo de WikiPathways (CC0) o desde cero. **Nunca** a partir de imágenes de KEGG o BioCyc.
4. Si corresponde, agrega casos de "verdades biológicas" con su referencia bibliográfica (sección 14 del manual).

## Escribir y revisar contenido

El contenido vive en `content/` como MDX y sigue la plantilla de la sección 10 del manual.

### Flujo editorial

| Estado | Quién | Qué significa |
| --- | --- | --- |
| Borrador | Autor | Texto escrito. Si se generó con apoyo de IA, se marca así hasta su revisión. |
| Revisado | Revisor con formación en el área | Revisión del *pull request* con la lista de verificación. |
| Validado | Segundo revisor, idealmente docente universitario | Aprobación final; la insignia muestra los nombres de quienes revisaron. |

### Lista de verificación de la revisión

- [ ] **Exactitud:** las afirmaciones son correctas y coinciden con las fuentes.
- [ ] **Referencias:** cada afirmación no trivial y cada cifra (rendimiento de ATP, ΔG) tiene su fuente.
- [ ] **Claridad:** frases de menos de 25 palabras y un concepto por párrafo.
- [ ] **Nivel:** el texto corresponde al nivel indicado (básico, intermedio o avanzado).
- [ ] **Nomenclatura:** forma iónica a pH fisiológico (piruvato, lactato) y nombre en inglés entre paréntesis la primera vez.
- [ ] **Atribución:** los textos adaptados de Reactome indican "adaptado y traducido de Reactome" con enlace.

## Reportar un error científico

Abre un *issue* con la URL de la página, qué dice la aplicación, qué debería decir y la fuente que lo respalda.

## Licencia de las contribuciones

Al contribuir aceptas que tu código se publique bajo la licencia [MIT](LICENSE) y tu contenido bajo [CC BY 4.0](LICENSE-content).
