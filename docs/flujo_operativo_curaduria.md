# Flujo operativo de curaduria

Fecha: 2026-06-21

Este documento describe el flujo operativo minimo para recibir, revisar y publicar testimonios ciudadanos en el mapa de Punto Cero.

## 1. Como llega un testimonio

1. La persona abre `captura.html`.
2. Completa los datos basicos, acepta el consentimiento y adjunta o graba un audio.
3. El audio se sube al bucket de Supabase Storage `testimonios-audio`, en ruta `pending/...`.
4. Los metadatos se insertan en la tabla `submissions`.
5. El registro queda con:
   - `status = pending`
   - `ethical_review_status = pending`
   - `curatorial_review_status = pending`

Mientras el testimonio esta pendiente, no aparece en el mapa publico.

## 2. Como entrar a curaduria

1. Abrir `curaduria.html` desde el enlace discreto del footer del mapa o escribiendo la ruta directamente.
2. Iniciar sesion con la cuenta administradora autorizada:
   - `gvalenzuela@somoseduk.org`
3. Usar la contrasena configurada en Supabase Auth.

Si el login funciona pero no se muestran registros, revisar:

- que la sesion pertenezca al correo administrador,
- que la funcion `public.is_testimony_admin()` use ese mismo correo,
- que el registro tenga `status = pending`,
- que no haya errores de RLS en la consola del navegador.

## 3. Como aprobar

1. En `curaduria.html`, escuchar el audio.
2. Revisar seudonimo, comunidad, municipio/localidad, descripcion y coordenadas.
3. Agregar notas internas si hace falta.
4. Presionar `Aprobar`.

La accion actualiza el registro con:

- `status = approved`
- `curatorial_review_status = approved`
- `reviewed_by = gvalenzuela@somoseduk.org`
- `reviewed_at`
- `curator = gvalenzuela@somoseduk.org`
- `curated_at`

Cuando queda aprobado, el registro aparece en `approved_testimonies_public` y el mapa lo carga automaticamente.

## 4. Como rechazar

1. En `curaduria.html`, revisar el testimonio.
2. Agregar una nota interna explicando la razon editorial o etica.
3. Presionar `Rechazar`.

La accion actualiza el registro con:

- `status = rejected`
- `curatorial_review_status = rejected`
- campos de revision y notas internas.

Los testimonios rechazados no aparecen en `approved_testimonies_public` ni en el mapa publico.

Si aparece el error `submissions_curatorial_review_status_check`, ejecutar en Supabase SQL Editor el archivo:

`supabase/fix_curatorial_review_status_check.sql`

Ese SQL permite los valores curatoriales `pending`, `approved` y `rejected`.

## 5. Como mantener pendiente

1. Usar `Mantener pendiente` cuando el testimonio requiere revision posterior.
2. El registro conserva o vuelve a:
   - `status = pending`
   - `curatorial_review_status = pending`
3. No se publica en el mapa.

## 6. Como aparece en el mapa

`index.html` carga dos fuentes:

- `SOUND_POINTS`: corpus historico base.
- `approved_testimonies_public`: testimonios ciudadanos aprobados desde Supabase.

El mapa solo integra filas con `status = approved`. Para cada testimonio aprobado:

1. Lee metadatos publicos desde `approved_testimonies_public`.
2. Valida latitud y longitud.
3. Genera una signed URL para reproducir el audio aprobado.
4. Agrega el punto al mapa sin duplicar testimonios ya cargados.
5. Actualiza el contador de la portada con el total real.

Si Supabase falla, el mapa mantiene el corpus local `SOUND_POINTS` como respaldo.

## 7. Que hacer si algo falla

### No se puede enviar desde captura

- Revisar que el proyecto Supabase este Healthy.
- Revisar que el bucket `testimonios-audio` exista.
- Revisar que la tabla `submissions` permita `INSERT` anon con `status = pending`.
- Revisar consola del navegador y respuesta de Storage/REST.

### No aparecen pendientes en curaduria

- Confirmar que el registro tenga `status = pending`.
- Confirmar que el login sea con `gvalenzuela@somoseduk.org`.
- Confirmar que `is_testimony_admin()` reconoce el email del JWT.
- Revisar errores RLS en consola.

### Aprobar o rechazar falla

- Si el error menciona `submissions_curatorial_review_status_check`, aplicar `supabase/fix_curatorial_review_status_check.sql`.
- Revisar que `curaduria.html` envie `curatorial_review_status` como `pending`, `approved` o `rejected`.
- Revisar que las politicas RLS permitan update al admin autenticado.

### Un aprobado no aparece en el mapa

- Confirmar que `status = approved`.
- Confirmar que aparece en `approved_testimonies_public`.
- Confirmar que tenga `latitude` y `longitude` validas.
- Confirmar que se pueda generar signed URL del audio.
- Recargar el mapa o esperar el refresco automatico.

### El contador no coincide

- El contador debe sumar `SOUND_POINTS` mas los testimonios aprobados cargados desde Supabase.
- Si Supabase falla, debe volver al conteo base de `SOUND_POINTS`.
