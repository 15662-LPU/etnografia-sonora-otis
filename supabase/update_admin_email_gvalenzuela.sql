-- Punto Cero / Comparte tu historia
-- Incremental SQL only: change the authorized curation admin email.
--
-- Run this in Supabase SQL Editor for project:
-- https://zopzhhqzuslyafznwhnc.supabase.co

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
is 'True only for the authenticated testimony curator account: gvalenzuela@somoseduk.org.';

commit;
