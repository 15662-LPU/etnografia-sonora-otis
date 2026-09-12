-- Expose non-personal participation categories on the public map feed.
-- These fields allow approved citizen audios to show labels such as
-- "Salud", "Docente" or "Rescatista" in the map card.

drop view if exists public.approved_testimonies_public;

create view public.approved_testimonies_public
with (security_invoker = true)
as
select
  id,
  status,
  public_name_or_alias,
  community,
  municipality,
  locality,
  place_label,
  description,
  testimony_type,
  tipo_relato,
  perfil_participante,
  interview_date,
  coordinate_type,
  latitude,
  longitude,
  audio_bucket,
  audio_path,
  audio_original_filename,
  audio_mime_type,
  audio_size_bytes,
  audio_duration_seconds,
  curated_at
from public.submissions
where status = 'approved';

grant select on public.approved_testimonies_public to anon;
grant select on public.approved_testimonies_public to authenticated;

grant select (
  id,
  status,
  public_name_or_alias,
  community,
  municipality,
  locality,
  place_label,
  description,
  testimony_type,
  tipo_relato,
  perfil_participante,
  interview_date,
  coordinate_type,
  latitude,
  longitude,
  audio_bucket,
  audio_path,
  audio_original_filename,
  audio_mime_type,
  audio_size_bytes,
  audio_duration_seconds,
  curated_at
) on public.submissions to anon;

comment on view public.approved_testimonies_public
is 'Public map feed. Contains only approved testimony fields safe for public display, including non-personal participation categories.';
