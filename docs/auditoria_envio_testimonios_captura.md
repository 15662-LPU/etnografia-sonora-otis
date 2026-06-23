# Auditoria del envio de testimonios en captura.html

Fecha: 2026-06-23

Alcance: revision local de `captura.html`, SQL local de Supabase y flujo de envio ciudadano. No se ejecuto ningun cambio en produccion, no se borraron datos y no se hizo push.

## Resumen ejecutivo

El bloqueo reportado por usuarios era consistente con este error:

```text
new row for relation "submissions" violates check constraint "submissions_testimony_type_check"
```

La causa mas probable es una divergencia de vocabulario:

- `testimony_type` es una columna legacy con valores historicos.
- El formulario actualizado empezo a enviar valores conceptuales nuevos: `personal`, `familiar`, `comunitario`, `institucional`.
- La base viva rechazo al menos uno de esos valores.

La correccion local conserva el modelo nuevo en `tipo_relato` y `perfil_participante`, pero traduce `testimony_type` a valores legacy compatibles antes del INSERT.

Ademas se encontraron riesgos de experiencia y consistencia:

- El formulario sube primero el audio y luego inserta la ficha. Si el INSERT falla, puede quedar un audio en Storage sin fila en `submissions`.
- El boton de envio no bloqueaba doble toque; en movil esto podia disparar envios paralelos.
- El mensaje visible exponia detalles tecnicos de Supabase.
- Las coordenadas opcionales no se validaban como par antes de subir audio.
- El repo local no contiene el `CREATE TABLE public.submissions`, por lo que los `NOT NULL` y todos los `CHECK` reales deben confirmarse en Supabase antes de deploy.

## Cambios locales aplicados

Archivo modificado:

```text
captura.html
```

Cambios:

1. Se agrego `legacyTestimonyType()` para que `testimony_type` no envie valores fuera del CHECK legacy.
2. Se agrego bloqueo de envio mientras hay una operacion en curso.
3. Se agrego cache local del audio ya subido para reintentar guardar la ficha sin subir otro audio.
4. Se agregaron mensajes de progreso: subida de audio y guardado de ficha.
5. Se dejaron mensajes de error comprensibles para usuarios, sin JSON tecnico de Supabase.
6. Se agrego validacion previa de coordenadas opcionales.
7. Si falla el envio, el registro tecnico conserva `last_error` y `last_error_stage`.

## Flujo auditado

### 1. Audio

Estado actual:

- El formulario no graba audio dentro del navegador.
- Recibe un archivo de audio mediante `<input type="file">`.
- Formatos permitidos: `mp3`, `m4a`, `wav`, `ogg`.
- Tamano maximo local: 100 MB.
- Ruta generada: `pending/<submission-id>/<timestamp>-<filename>`.

Compatibilidad Storage local:

- Bucket esperado: `testimonios-audio`.
- Politica local permite `INSERT` anon solo cuando la primera carpeta es `pending`.
- La ruta generada por `captura.html` cumple esa politica.

Riesgo pendiente:

- Storage y Postgres no forman una transaccion unica. Siempre puede existir un hueco entre audio subido y ficha guardada.
- La mejora local reduce duplicados en reintentos, pero no elimina la posibilidad de un audio huerfano si el usuario abandona tras un fallo de INSERT.

### 2. Tipo de relato y perfil

Formulario:

```text
tipo_relato: personal | familiar | comunitario | institucional
perfil_participante: habitante_comunidad | estudiante | docente | medico | ...
```

Payload actual:

```text
testimony_type: valor legacy compatible
tipo_relato: valor conceptual nuevo
perfil_participante: perfil detallado
```

Mapeo legacy aplicado:

```text
perfil legacy permitido -> usa perfil_participante
relato legacy permitido -> usa tipo_relato
si no coincide -> otro
```

Valores legacy cubiertos:

```text
comunitario
familiar
productor_rural
pescador
comerciante
estudiante
servidor_publico
otro
```

Esto evita que `personal` e `institucional` rompan `submissions_testimony_type_check`.

### 3. Consentimientos

Campos requeridos por formulario:

```text
consent_archive_pending_review = true
consent_understands_not_auto_published = true
```

Campos opcionales:

```text
consent_may_request_more_information
consent_may_consider_publication_after_review
```

Compatibilidad local:

- El payload siempre envia los campos booleanos.
- El estado publico del testimonio sigue siendo `pending`.
- No hay publicacion automatica.

Riesgo pendiente:

- Confirmar en Supabase si algun consentimiento tiene `NOT NULL` o CHECK adicional no documentado localmente.

### 4. Coordenadas

Campos:

```text
latitude
longitude
coordinate_type
contains_sensitive_location
```

Estado corregido:

- Las coordenadas siguen siendo opcionales.
- Si se captura una sola coordenada, un valor invalido o fuera de rango, el formulario detiene el envio antes de subir audio.

Compatibilidad local:

- `coordinate_type` envia uno de estos valores:

```text
approximate
exact
symbolic
sensitive_displaced
unknown
```

Riesgo pendiente:

- Confirmar en Supabase que el CHECK real de `coordinate_type` acepte todos esos valores.

### 5. Insercion en submissions

Payload minimo operativo:

```text
id
status = pending
capture_mode = public_web
source_page = captura.html
public_name_or_alias
interviewer
interview_date
community
municipality
locality
place_label
description
testimony_type
tipo_relato
perfil_participante
audio_bucket = testimonios-audio
audio_path
audio_original_filename
audio_mime_type
audio_size_bytes
consent_*
ethical_review_status = pending
curatorial_review_status = pending
```

Compatibilidad RLS local:

```text
status = pending
capture_mode = public_web
```

El payload cumple ambas condiciones.

Riesgo pendiente:

- La tabla real puede tener columnas obligatorias o CHECKs no presentes en el repo local.
- La verificacion definitiva debe hacerse con consultas de solo lectura en Supabase SQL Editor.

## Campos especialmente revisados

| Campo | Estado local | Riesgo |
| --- | --- | --- |
| `testimony_type` | Corregido con mapeo legacy | Confirmar CHECK vivo |
| `tipo_relato` | Enviado como valor nuevo | Confirmar columna existe en produccion |
| `perfil_participante` | Enviado como perfil detallado | Confirmar columna existe en produccion |
| consentimiento | Dos checks requeridos y dos opcionales | Confirmar NOT NULL reales |
| coordenadas | Opcionales con validacion local | Confirmar CHECK vivo de `coordinate_type` |
| `audio_url` | No se usa en este flujo | No aplica |
| `storage_path` | No se usa con ese nombre | El equivalente operativo es `audio_path` |
| `audio_path` | Enviado con prefijo `pending/` | Compatible con politica local de Storage |

## Diagnostico de Supabase recomendado

Ejecutar manualmente en Supabase SQL Editor. Son consultas de lectura, no modifican datos.

### Columnas y obligatoriedad

```sql
select
  column_name,
  data_type,
  is_nullable,
  column_default
from information_schema.columns
where table_schema = 'public'
  and table_name = 'submissions'
order by ordinal_position;
```

### CHECK constraints reales

```sql
select
  conname,
  pg_get_constraintdef(oid) as definition
from pg_constraint
where conrelid = 'public.submissions'::regclass
order by conname;
```

### Politicas RLS reales

```sql
select
  schemaname,
  tablename,
  policyname,
  cmd,
  roles,
  qual,
  with_check
from pg_policies
where schemaname = 'public'
  and tablename = 'submissions'
order by policyname;
```

### Bucket y politicas de Storage

```sql
select
  id,
  name,
  public,
  created_at
from storage.buckets
where id = 'testimonios-audio';
```

```sql
select
  schemaname,
  tablename,
  policyname,
  cmd,
  roles,
  qual,
  with_check
from pg_policies
where schemaname = 'storage'
  and tablename = 'objects'
  and policyname like 'testimonios_audio_%'
order by policyname;
```

## Deteccion de audios huerfanos

Consulta segura de solo lectura:

```sql
select
  o.name as audio_path,
  o.bucket_id,
  o.created_at,
  o.updated_at,
  o.metadata,
  s.id as submission_id
from storage.objects o
left join public.submissions s
  on s.audio_bucket = o.bucket_id
 and s.audio_path = o.name
where o.bucket_id = 'testimonios-audio'
  and o.name like 'pending/%'
  and s.id is null
order by o.created_at desc;
```

Revisar antes de cualquier limpieza:

```text
1. Exportar la lista.
2. Separar objetos recientes de objetos antiguos.
3. No borrar objetos de las ultimas 24-48 horas.
4. Buscar si existe respaldo JSON descargado por usuario.
5. Confirmar que no hay fila en submissions con ese audio_path.
6. Solo despues, preparar limpieza con autorizacion explicita.
```

## Propuesta segura de limpieza

No ejecutar sin autorizacion.

En vez de borrar directo desde SQL, usar Storage API con service role en un entorno controlado. El script debe tener modo dry-run por defecto:

```text
1. Leer lista de huerfanos con la consulta anterior.
2. Filtrar por antiguedad minima, por ejemplo mas de 48 horas.
3. Mostrar conteo y rutas exactas.
4. Exigir una bandera explicita, por ejemplo --confirm-delete.
5. Eliminar solo esas rutas del bucket testimonios-audio.
6. Guardar log local de rutas eliminadas.
```

No se recomienda borrar objetos recientes porque pueden corresponder a un envio en proceso o a un reintento manual.

## Pruebas locales realizadas

Ejecutadas localmente:

```powershell
git diff --check -- captura.html docs/auditoria_envio_testimonios_captura.md
node -e "const fs=require('fs'); const html=fs.readFileSync('captura.html','utf8'); const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]); for (const script of scripts) new Function(script); console.log('scripts parsed:', scripts.length);"
```

Resultado:

```text
Sin errores de whitespace en los archivos tocados.
JavaScript embebido parseado correctamente.
```

Pruebas que no se hicieron por restriccion:

- No se subio audio real a Storage.
- No se inserto fila en `submissions`.
- No se ejecuto limpieza.
- No se hizo deploy.

## Recomendaciones prioritarias antes de deploy

1. Ejecutar las consultas diagnosticas de columnas y CHECKs en Supabase.
2. Confirmar que `submissions_testimony_type_check` acepta los valores legacy usados por `legacyTestimonyType()`.
3. Confirmar que `tipo_relato` y `perfil_participante` existen en produccion.
4. Confirmar que `coordinate_type` acepta `approximate`, `exact`, `symbolic`, `sensitive_displaced`, `unknown`.
5. Hacer una prueba controlada con un audio pequeno y verificar:

```text
audio en testimonios-audio/pending/
fila en submissions
status = pending
capture_mode = public_web
audio_path coincide con storage.objects.name
```

6. Si la prueba controlada falla despues de subir audio, no repetir muchas veces: usar la consulta de huerfanos para identificar el objeto y revisar la causa del INSERT.

## Criterio de listo para deploy

El cambio queda listo para revision cuando:

- `git diff --check` no reporte errores.
- Las consultas de Supabase confirmen compatibilidad.
- Una prueba controlada genere una fila `pending`.
- El mensaje final para usuario sea comprensible y no exponga JSON tecnico.
- No haya cambios en `curaduria.html` ni `index.html`.
