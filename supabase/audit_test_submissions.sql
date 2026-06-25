-- Punto Cero / auditoria y separacion de envios de prueba.
--
-- Uso:
-- 1. Ejecutar primero los bloques de auditoria.
-- 2. Revisar manualmente los candidatos.
-- 3. Ejecutar el bloque UPDATE solo cuando los candidatos sean pruebas tecnicas.
--
-- Este archivo no borra filas ni audios.

-- 1) Auditoria general de envios.
select
  id,
  created_at,
  status,
  public_name_or_alias,
  community,
  municipality,
  interview_date,
  audio_original_filename,
  audio_size_bytes,
  description
from public.submissions
order by created_at desc;

select status, count(*) as total
from public.submissions
group by status
order by status;

-- 2) Candidatos probables a prueba tecnica.
with test_candidates as (
  select
    s.*,
    (
      coalesce(public_name_or_alias, '') ilike 'An_nimo'
      or coalesce(public_name_or_alias, '') = 'Prueba curaduria Codex'
      or coalesce(audio_original_filename, '') ilike any (array[
        '%historia-punto-cero%',
        '%curaduria-test%',
        '%test%',
        '%prueba%'
      ])
      or coalesce(description, '') ilike any (array[
        '%historia enviada en audio para revisi_n%',
        '%prueba%',
        '%test%'
      ])
      or coalesce(community, '') ilike '%prueba%'
    ) as probable_test
  from public.submissions s
)
select
  id,
  created_at,
  status,
  public_name_or_alias,
  community,
  municipality,
  interview_date,
  audio_original_filename,
  audio_size_bytes,
  description,
  admin_notes,
  curatorial_notes
from test_candidates
where probable_test
order by created_at desc;

-- 3) Vista temporal de medicion desde cero, sin crear objetos permanentes.
with classified as (
  select
    s.*,
    (
      coalesce(admin_notes, '') ilike '%PRUEBA TECNICA%'
      or coalesce(curatorial_notes, '') ilike '%PRUEBA TECNICA%'
      or coalesce(public_name_or_alias, '') ilike 'An_nimo'
      or coalesce(public_name_or_alias, '') = 'Prueba curaduria Codex'
      or coalesce(audio_original_filename, '') ilike any (array[
        '%historia-punto-cero%',
        '%curaduria-test%',
        '%test%',
        '%prueba%'
      ])
      or coalesce(description, '') ilike any (array[
        '%historia enviada en audio para revisi_n%',
        '%prueba%',
        '%test%'
      ])
      or coalesce(community, '') ilike '%prueba%'
    ) as is_technical_test
  from public.submissions s
)
select
  count(*) as envios_totales,
  count(*) filter (where not is_technical_test) as envios_reales,
  count(*) filter (where is_technical_test) as pruebas_tecnicas,
  count(*) filter (where status = 'pending' and not is_technical_test) as pendientes_reales,
  count(*) filter (where status = 'approved' and not is_technical_test) as aprobados_reales,
  count(*) filter (where status = 'rejected') as rechazados_totales
from classified;

select
  status,
  case
    when (
      coalesce(admin_notes, '') ilike '%PRUEBA TECNICA%'
      or coalesce(curatorial_notes, '') ilike '%PRUEBA TECNICA%'
      or coalesce(public_name_or_alias, '') ilike 'An_nimo'
      or coalesce(public_name_or_alias, '') = 'Prueba curaduria Codex'
      or coalesce(audio_original_filename, '') ilike any (array[
        '%historia-punto-cero%',
        '%curaduria-test%',
        '%test%',
        '%prueba%'
      ])
      or coalesce(description, '') ilike any (array[
        '%historia enviada en audio para revisi_n%',
        '%prueba%',
        '%test%'
      ])
      or coalesce(community, '') ilike '%prueba%'
    )
    then 'prueba_tecnica'
    else 'posible_real'
  end as clasificacion,
  count(*) as total
from public.submissions
group by status, clasificacion
order by status, clasificacion;

-- 4) Deteccion de audios huerfanos. Solo lectura.
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

-- 5) Limpieza logica: marcar pruebas tecnicas como rejected.
-- Ejecutar este bloque solo despues de revisar los candidatos.
-- No borra filas ni audios.
--
-- Importante:
-- No se actualiza automaticamente por heuristica para evitar marcar un
-- testimonio anonimo real como prueba. Copia aqui solo los IDs confirmados.
begin;

with selected_test_ids(id) as (
  values
    -- Reemplazar por IDs confirmados, por ejemplo:
    -- ('00000000-0000-0000-0000-000000000000'::uuid)
    (null::uuid)
),
candidates as (
  select id
  from selected_test_ids
  where id is not null
)
update public.submissions s
set
  status = 'rejected',
  curatorial_review_status = 'rejected',
  curatorial_notes = trim(both from concat_ws(
    E'\n',
    nullif(s.curatorial_notes, ''),
    'PRUEBA TECNICA - no contabilizar como participacion ciudadana real'
  )),
  admin_notes = trim(both from concat_ws(
    E'\n',
    nullif(s.admin_notes, ''),
    'PRUEBA TECNICA - no contabilizar como participacion ciudadana real'
  )),
  curated_at = coalesce(s.curated_at, now())
from candidates c
where s.id = c.id
returning
  s.id,
  s.created_at,
  s.status,
  s.public_name_or_alias,
  s.community,
  s.audio_original_filename,
  s.admin_notes;

-- Si el resultado no es correcto, ejecutar rollback.
-- Si el resultado es correcto, cambiar rollback por commit y ejecutar de nuevo.
rollback;
-- commit;

-- 6) Validacion posterior.
select status, count(*) as total
from public.submissions
group by status
order by status;

select id, created_at, status, public_name_or_alias, community, audio_original_filename
from public.submissions
where status = 'pending'
order by created_at desc;

select id, status, public_name_or_alias, community, municipality, audio_path, curated_at
from public.approved_testimonies_public
order by curated_at desc;
