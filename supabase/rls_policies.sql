-- Punto Cero / Comparte tu historia
-- Secure minimal RLS policies for testimony review and publication.
--
-- Run this in Supabase SQL Editor for project:
-- https://zopzhhqzuslyafznwhnc.supabase.co
--
-- Admin authorized for curation:
-- gvalenzuela@somoseduk.org
--
-- Goal:
-- - anon can insert pending submissions from captura.html.
-- - anon can read only approved public-safe fields via approved_testimonies_public.
-- - authenticated admin can read all submissions and update review fields.
-- - storage accepts public uploads only under pending/.
-- - public audio playback uses signed URLs only for approved submissions.

begin;

create or replace function public.is_testimony_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select lower(coalesce(auth.jwt() ->> 'email', '')) = 'gvalenzuela@somoseduk.org';
$$;

comment on function public.is_testimony_admin()
is 'True only for the authenticated testimony curator account.';

alter table public.submissions enable row level security;

drop policy if exists "submissions_anon_insert_pending" on public.submissions;
drop policy if exists "submissions_anon_select_approved" on public.submissions;
drop policy if exists "submissions_admin_select_all" on public.submissions;
drop policy if exists "submissions_admin_update_review" on public.submissions;

-- Remove broad privileges first. Re-grant only the minimum needed below.
revoke all on table public.submissions from anon;
revoke all on table public.submissions from authenticated;

-- Public capture form: insert only records that start as pending.
grant insert on table public.submissions to anon;

create policy "submissions_anon_insert_pending"
on public.submissions
for insert
to anon
with check (
  status = 'pending'
  and capture_mode = 'public_web'
);

-- Admin panel: authenticated curator can read every row.
grant select on table public.submissions to authenticated;

create policy "submissions_admin_select_all"
on public.submissions
for select
to authenticated
using (public.is_testimony_admin());

-- Admin panel: authenticated curator can update only review/publication columns.
-- Column-level grants below prevent changing the submitted testimony payload.
grant update (
  status,
  reviewed_by,
  reviewed_at,
  ethical_review_status,
  ethical_notes,
  curatorial_review_status,
  curatorial_notes,
  curator,
  curated_at,
  admin_notes
) on public.submissions to authenticated;

create policy "submissions_admin_update_review"
on public.submissions
for update
to authenticated
using (public.is_testimony_admin())
with check (
  public.is_testimony_admin()
  and status in ('pending', 'approved', 'rejected')
);

-- Public-safe view for the map.
-- The map should read this view, not public.submissions directly.
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

comment on view public.approved_testimonies_public
is 'Public map feed. Contains only approved testimony fields safe for public display.';

-- Public approved rows can be selected only through safe columns.
-- This supports both the public view and storage policies that cross-check
-- approved audio_path.
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

create policy "submissions_anon_select_approved"
on public.submissions
for select
to anon
using (status = 'approved');

-- Storage policies for testimonios-audio.
-- The bucket is expected to exist already.
-- Files uploaded by captura.html use paths like:
-- pending/<submission-id>/<timestamp>-filename.wav

drop policy if exists "testimonios_audio_anon_upload_pending" on storage.objects;
drop policy if exists "testimonios_audio_public_read_approved" on storage.objects;
drop policy if exists "testimonios_audio_admin_read_all" on storage.objects;

-- Public form may upload only to pending/.
create policy "testimonios_audio_anon_upload_pending"
on storage.objects
for insert
to anon
with check (
  bucket_id = 'testimonios-audio'
  and (storage.foldername(name))[1] = 'pending'
);

-- Public playback: allow reading only objects linked to approved submissions.
-- Frontend should request a signed URL for approved audio_path and use that URL
-- in the audio player. This keeps pending/rejected audio private.
create policy "testimonios_audio_public_read_approved"
on storage.objects
for select
to anon
using (
  bucket_id = 'testimonios-audio'
  and exists (
    select 1
    from public.submissions s
    where s.status = 'approved'
      and s.audio_bucket = 'testimonios-audio'
      and s.audio_path = storage.objects.name
  )
);

-- Admin can play/review all uploaded audio after logging in.
create policy "testimonios_audio_admin_read_all"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'testimonios-audio'
  and public.is_testimony_admin()
);

commit;

-- Manual smoke tests after running this SQL:
--
-- 1) In captura.html, submit a new audio. It should insert status = pending.
-- 2) As anon, this should return rows only after something is approved:
--    GET /rest/v1/approved_testimonies_public?select=*
-- 3) As admin gvalenzuela@somoseduk.org, curaduria.html can:
--    GET /rest/v1/submissions?status=eq.pending&select=*
--    PATCH /rest/v1/submissions?id=eq.<id> { "status": "approved", ... }
-- 4) For approved rows, the map should create a signed URL for audio_path:
--    POST /storage/v1/object/sign/testimonios-audio/<audio_path>
