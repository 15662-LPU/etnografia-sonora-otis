-- Punto Cero / Analitica basica de investigacion
--
-- Ejecutar en Supabase SQL Editor.
--
-- Objetivo:
-- - registrar eventos anonimos de uso del sitio;
-- - permitir INSERT publico solo para eventos conocidos;
-- - permitir SELECT solo al admin autenticado via public.is_testimony_admin().

begin;

create table if not exists public.analytics_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  point_id text null,
  created_at timestamptz not null default now(),
  session_id text not null,
  user_agent text null,
  constraint analytics_events_event_type_check
    check (event_type in (
      'visit_home',
      'visit_map',
      'open_point',
      'play_audio',
      'submit_testimony'
    )),
  constraint analytics_events_session_id_check
    check (char_length(session_id) between 8 and 120),
  constraint analytics_events_user_agent_check
    check (user_agent is null or char_length(user_agent) <= 500)
);

alter table public.analytics_events enable row level security;

drop policy if exists "analytics_events_anon_insert" on public.analytics_events;
drop policy if exists "analytics_events_admin_select" on public.analytics_events;

grant insert on table public.analytics_events to anon;
grant select on table public.analytics_events to authenticated;

create policy "analytics_events_anon_insert"
on public.analytics_events
for insert
to anon
with check (
  event_type in (
    'visit_home',
    'visit_map',
    'open_point',
    'play_audio',
    'submit_testimony'
  )
  and session_id is not null
  and char_length(session_id) between 8 and 120
);

create policy "analytics_events_admin_select"
on public.analytics_events
for select
to authenticated
using (public.is_testimony_admin());

create index if not exists analytics_events_created_at_idx
on public.analytics_events (created_at desc);

create index if not exists analytics_events_event_type_created_at_idx
on public.analytics_events (event_type, created_at desc);

comment on table public.analytics_events
is 'Eventos anonimos de uso para investigacion y evaluacion del proyecto Punto Cero.';

commit;
