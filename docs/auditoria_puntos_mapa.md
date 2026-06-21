# Auditoria de calidad de SOUND_POINTS y propuesta de administracion

Fecha: 2026-06-21

Alcance: revision de los 61 elementos incrustados en `SOUND_POINTS` dentro de `index.html`.

No se modificaron coordenadas, enlaces, categorias, Supabase ni `curaduria.html`.

## Resumen ejecutivo

El arreglo `SOUND_POINTS` contiene 61 puntos historicos. La validacion automatica encontro que:

- No hay coordenadas fuera de rango.
- No hay pares lat/lng invertidos de forma evidente.
- No hay puntos sin medio asociado.
- No hay URLs duplicadas.
- Hay 1 par de coordenadas exactamente duplicado.
- Hay 1 posible duplicado semantico por titulo normalizado.
- Hay varios puntos que usan una ubicacion territorial de Guerrero aunque la fuente parece producida por medios, podcasts o musica externos.
- Hay puntos en costa, bahia o zona generica de Guerrero que requieren revision cartografica fina antes de corregir.

Decision curatorial posterior: no migrar los puntos historicos a Supabase. `SOUND_POINTS` se mantiene como corpus curado base en `index.html`; `curaduria.html` queda reservado para testimonios ciudadanos nuevos.

## Metodo

Se extrajo `SOUND_POINTS` desde `index.html` y se revisaron:

- Rango de coordenadas: longitud entre -180 y 180, latitud entre -90 y 90.
- Posible inversion lat/lng.
- Duplicados exactos de coordenadas.
- Duplicados normalizados de titulo.
- Duplicados de URL de Spotify/audio.
- Ausencia de `spotify` o `audio`.
- Puntos con ubicacion declarada generica.
- Separacion conceptual entre lugar de produccion y lugar del contenido.

Nota: la deteccion de "puntos en el mar" requiere una verificacion GIS o visual sobre mapa base con costa/bahia. Esta auditoria marca candidatos, no corrige ubicaciones.

## Hallazgos de datos

### Conteo

| Revision | Resultado |
| --- | --- |
| Total de puntos base | 61 |
| Coordenadas invalidas | 0 |
| Lat/lng posiblemente invertidas | 0 |
| Puntos sin audio/Spotify | 0 |
| URLs duplicadas | 0 |
| Coordenadas exactas duplicadas | 1 grupo |
| Titulos posiblemente duplicados | 1 grupo |

### Coordenadas duplicadas exactas

| Coordenada | IDs | Observacion |
| --- | --- | --- |
| `[-99.8945, 16.8531]` | 2, 30 | Ambos se ubican en Acapulco. No necesariamente es error, pero puede provocar sobreposicion visual y conviene separar ligeramente o asignar coordenada mas especifica. |

### Posible duplicado semantico

| IDs | Titulos | Observacion |
| --- | --- | --- |
| 42, 56 | `EL HURACAN OTIS (podcast estudiantil)` / `el huracan otis (podcast estudiantil)` | Parecen pertenecer a la misma familia de contenido. ID 42 apunta a un `show`; ID 56 apunta a un `episode`. Revisar si deben coexistir como serie y episodio o si uno debe ocultarse. |

### Enlaces que requieren revision editorial

No hay URLs duplicadas ni URLs de Spotify con formato invalido. Sin embargo:

| ID | Tipo de enlace | Observacion |
| --- | --- | --- |
| 42 | Spotify `show` | Puede abrir una serie completa, no un episodio especifico. Verificar si eso es intencional. |
| 58 | Spotify `show` | Puede abrir una serie completa, no un episodio especifico. Verificar si eso es intencional. |
| 61 | Spotify `show` | Puede abrir una serie completa, no un episodio especifico. Verificar si eso es intencional. |
| 28 | SharePoint embed | Funciona como audio externo, pero no esta normalizado como Spotify ni como Storage Supabase. Conviene migrarlo a un campo `audio_url` o a Storage si se quiere gobernanza uniforme. |

### Puntos candidatos a revision por costa, bahia o mar

Estos puntos no se corrigen automaticamente. Se marcan porque sus coordenadas caen en zonas costeras, bahia, playa, laguna o coordenadas genericas cercanas al borde marino. Requieren verificacion visual con mapa base o capa de costa.

| ID | Ubicacion | Coordenadas | Motivo |
| --- | --- | --- | --- |
| 5 | Zona Diamante, Acapulco | `[-99.86, 16.79]` | Zona costera/lagunar; revisar si cae sobre tierra, playa, laguna o mar. |
| 10 | Acapulco de Juarez | `[-99.91, 16.82]` | Coordenada muy costera; revisar sobre bahia/costa. |
| 14 | Acapulco | `[-99.88, 16.835]` | Posible bahia o borde costero; revisar. |
| 28 | Costa de Guerrero - Punto de Impacto | `[-99.76, 16.79]` | Punto simbolico de impacto; revisar si se quiere en mar, costa o tierra. |
| 33 | Acapulco - Bahia | `[-99.91, 16.85]` | El propio lugar dice bahia; puede ser intencional, pero conviene marcarlo como `content_place` y no necesariamente como produccion. |
| 37 | Acapulco | `[-99.89, 16.83]` | Posible zona de bahia; revisar. |
| 38 | Acapulco | `[-99.91, 16.84]` | Posible zona de bahia/costa; revisar. |
| 45 | Guerrero | `[-99.93, 16.83]` | Ubicacion generica; coordenada costera asignada editorialmente. |
| 51 | Guerrero | `[-99.91, 16.83]` | Ubicacion generica; coordenada costera asignada editorialmente. |
| 55 | Guerrero | `[-99.90, 16.82]` | Ubicacion generica; coordenada costera asignada editorialmente. |
| 57 | Guerrero | `[-99.92, 16.84]` | Ubicacion generica; coordenada costera asignada editorialmente. |
| 60 | Acapulco | `[-99.86, 16.82]` | Posible zona costera/lagunar; revisar. |

### Puntos con ubicacion generica de Guerrero

Estos puntos no tienen una localidad precisa o usan una ubicacion editorial amplia. Conviene separarlos en `content_place` y `production_place`.

| ID | Titulo | Ubicacion actual | Observacion |
| --- | --- | --- | --- |
| 40 | Huracan Otis suma muertos, desaparecidos y danos... | Guerrero | Coordenada cae cerca de Chilpancingo; el contenido habla de Acapulco y varios municipios. |
| 45 | El Huracan Otis (corrido) | Guerrero | Musica; revisar lugar de produccion/artista vs. lugar del contenido. |
| 47 | Huracan 'Otis': esta es la razon... | Costa de Guerrero | Medio nacional; revisar si el punto debe representar costa/impacto o produccion. |
| 51 | OTIS (cumbia) | Guerrero | Musica; revisar lugar de produccion/artista vs. lugar del contenido. |
| 55 | El Huracan Otis (Chuy Diaz) | Guerrero | Musica regional; revisar lugar de produccion/artista. |
| 57 | Corrido del Huracan Otis / Laurita Garza / Aquilino Petatan | Guerrero | Musica regional; revisar lugar de produccion/artista. |

### Fuentes ubicadas en Guerrero aunque podrian ser producciones externas

Este no es necesariamente un error. El mapa parece mezclar dos logicas:

1. Lugar de produccion de la pieza sonora.
2. Lugar al que refiere el contenido.

Casos a revisar con prioridad:

| ID | Fuente | Ubicacion actual | Riesgo |
| --- | --- | --- | --- |
| 34 | Primera Plana: Noticias | Acapulco, Guerrero | Puede ser nota producida fuera y contenido sobre Acapulco. |
| 36 | Primera Plana: Noticias | Acapulco, Guerrero | Igual que ID 34. |
| 38 | Cafeina x Sopitas.com | Acapulco, Guerrero | Medio probablemente externo; revisar produccion vs contenido. |
| 41 | La Formula es el Turismo | Acapulco, Guerrero | Puede ser fuente externa con contenido sobre Acapulco. |
| 47 | MVS Noticias - Luis Cardenas | Costa de Guerrero | Produccion probablemente nacional; contenido meteorologico/costa. |
| 48 | Ciro Gomez Leyva por la Manana | Acapulco, Guerrero | Produccion probablemente nacional; contenido sobre Acapulco. |
| 52 | MICRODOSIS EDUCATIVA KIDS | Acapulco, Guerrero | Revisar si es produccion local o contenido educativo externo. |
| 61 | Lia Alfaro | Acapulco, Guerrero | Enlace de tipo show; revisar episodio especifico y lugar de produccion. |

### Problemas de texto/normalizacion

Hay cadenas con caracteres mojibake o encoding no normalizado, visibles como `â€”` en algunos titulos/recorders. Ejemplos:

- ID 8: `Huracan Otis â€” Derecho en Contexto`
- ID 12: `Huracan Otis â€“ Resiliencia Guerrero`
- ID 19: `Reflexiones despues del Huracan Otis â€” ...`
- ID 27: `Huracan Otis â€” Pavel Salinas...`

No se corrigieron en esta auditoria.

## Decision tecnica posterior

No se creara tabla `map_points` y no se migraran los 61 puntos historicos a Supabase.

Alcance confirmado:

- `SOUND_POINTS` sigue siendo el corpus historico curado base.
- Las correcciones editoriales de historicos se hacen de forma controlada en `index.html`.
- `curaduria.html` administra solo testimonios ciudadanos nuevos guardados en `submissions`.
- El mapa publico combina `SOUND_POINTS` con filas aprobadas de `approved_testimonies_public`.

## Regla curatorial aplicada a historicos

Para fuentes de Spotify, radio, podcast o medios nacionales, el punto debe representar el lugar de produccion, grabacion, publicacion o emision del audio, no necesariamente el lugar del contenido narrado.

Correccion ya aplicada:

| ID | Fuente | Nueva ubicacion editorial | Motivo |
| --- | --- | --- | --- |
| 38 | Cafeina x Sopitas.com | Ciudad de Mexico | Produccion externa; contenido sobre Acapulco/Otis. |
| 47 | MVS Noticias - Luis Cardenas | Ciudad de Mexico | Produccion externa; contenido sobre Acapulco/Otis. |
| 48 | Ciro Gomez Leyva por la Manana | Ciudad de Mexico | Produccion externa; contenido sobre Acapulco/Otis. |

Pendiente:

| ID | Fuente | Estado |
| --- | --- | --- |
| 41 | La Formula es el Turismo | No se movio porque no se confirmo con suficiente evidencia que pertenezca a Radio Formula nacional. |
| 42 | Podcast estudiantil | Usa Spotify `show`; revisar si conviene episodio especifico. |
| 58 | Podcast/show | Usa Spotify `show`; revisar si conviene episodio especifico. |
| 61 | Lia Alfaro | Usa Spotify `show`; revisar si conviene episodio especifico. |

## Proximos pasos sugeridos

1. Ejecutar una revision visual de los candidatos costeros en mapa base.
2. Decidir para cada caso si la coordenada representa produccion, contenido o punto simbolico.
3. Corregir historicos en lotes pequenos y con commit propio.
4. Mantener `curaduria.html` solo para testimonios ciudadanos nuevos.
