# Corrección de audios duplicados

Fecha: 2026-10-14.

## Comportamiento

El mapa identifica los testimonios por la huella SHA-256 del archivo, aunque tengan rutas o nombres diferentes. Cada grupo de archivos idénticos publica un solo punto. Los archivos y registros de Supabase permanecen intactos.

`data/audio-fingerprints.json` contiene las huellas verificadas de los 23 archivos públicos existentes. El mapa consulta ese índice para no descargar los 129 MB del corpus al abrirlo. Si aparece un archivo nuevo, calcula su huella mediante acceso firmado, con dos lectores como máximo y reutilización durante la sesión. Los archivos cuyo contenido no puede verificarse permanecen fuera del mapa hasta un refresco satisfactorio. Las URLs firmadas no se guardan en el índice.

El índice presupone que las rutas UUID de los audios son inmutables. Si se reemplaza un objeto en su misma ruta, debe renovarse su entrada; un cambio de tamaño ya obliga a verificar de nuevo.

## Representantes de los duplicados existentes

- M4A: se conserva `397cd3a0-382b-43ab-965b-ed19028a46be`; se omite `a971be2d-10f2-452f-916a-4c0a635820f6`.
- WAV del par hospitalario: se conserva `00ced058-392a-4c4d-9b3d-efcb8227e724`; se omite `2e9b48f3-266c-485e-970f-c3a0f580797c`.
- WAV con dos registros fuera de Acapulco: se conserva el primer registro según fecha de curaduría y, en caso de empate, ID.

Los dos representantes explícitos conservan las coordenadas urbanas ya existentes. No se inventaron coordenadas hospitalarias ni se modificaron etiquetas en la base de datos. La validación de la sede hospitalaria sigue siendo una tarea curatorial independiente.

El testimonio propio de Bienes Comunales de Cacahuatepec (`432871f9-2d90-4d89-bed8-c5488a838823`) es diferente y sigue visible. Los registros con coordenadas nulas, vacías o fuera de rango no generan puntos. El corpus aprobado actual produce 19 testimonios únicos con coordenadas válidas; junto con los 61 puntos base, el mapa cuenta 80 piezas.

## Diagnóstico de operación

En consola:

- `window.PUNTO_CERO_AUDIO_DUPLICATES`: copias omitidas, representante y huella.
- `window.PUNTO_CERO_UNVERIFIED_AUDIO_IDS`: registros pendientes de verificación del archivo.
- `window.PUNTO_CERO_APPROVED_TESTIMONIES`: testimonios efectivamente publicados en el mapa.

Para cambiar un representante confirmado, ajustar `preferred_submission_ids` del índice usando la huella del grupo y el ID completo del registro. Si no existe un representante explícito, la selección es estable por fecha de curaduría e ID; solo participan registros con coordenadas válidas y audio verificado.

## Validación

`node --test tests/audio-deduplication.test.mjs` comprueba duplicación de contenido con nombres diferentes, conservación de archivos distintos con nombres iguales, coordenadas inválidas, reintentos, caché de sesión, invalidación por tamaño, identificadores sensibles a mayúsculas y el corpus público de referencia.

`node tests/audio-deduplication-browser.mjs <URL>` comprueba la publicación de 19 testimonios únicos, los tres representantes omitidos, el testimonio de Cacahuatepec conservado, el conteo de 80 piezas, la fuente del mapa y la reproducción del WAV retenido en móvil y escritorio. Esta prueba del corpus de referencia debe actualizarse si se aprueban nuevos testimonios.
