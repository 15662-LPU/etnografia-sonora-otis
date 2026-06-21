-- Punto Cero / Comparte tu historia
-- Incremental SQL only: align curatorial_review_status CHECK with curation UI.
--
-- Problem:
-- curaduria.html sends:
-- - status = 'approved'  and curatorial_review_status = 'approved'  when approving
-- - status = 'rejected'  and curatorial_review_status = 'rejected'  when rejecting
-- - status = 'pending'   and curatorial_review_status = 'pending'   when keeping pending
--
-- The live constraint submissions_curatorial_review_status_check currently rejects
-- curatorial_review_status = 'rejected'. This SQL does not change RLS policies,
-- does not update existing testimonies, and only aligns the CHECK vocabulary.

begin;

-- 1) Inspect current relevant CHECK constraints.
select
  conname,
  pg_get_constraintdef(oid) as definition
from pg_constraint
where conrelid = 'public.submissions'::regclass
  and conname in (
    'submissions_status_check',
    'submissions_ethical_review_status_check',
    'submissions_curatorial_review_status_check'
  )
order by conname;

-- 2) Inspect current values already present in the table.
select 'status' as column_name, status as value, count(*) as rows
from public.submissions
group by status
union all
select 'ethical_review_status' as column_name, ethical_review_status as value, count(*) as rows
from public.submissions
group by ethical_review_status
union all
select 'curatorial_review_status' as column_name, curatorial_review_status as value, count(*) as rows
from public.submissions
group by curatorial_review_status
order by column_name, value;

-- 3) Replace only the incompatible CHECK.
alter table public.submissions
drop constraint if exists submissions_curatorial_review_status_check;

alter table public.submissions
add constraint submissions_curatorial_review_status_check
check (
  curatorial_review_status is null
  or curatorial_review_status in ('pending', 'approved', 'rejected')
);

comment on constraint submissions_curatorial_review_status_check on public.submissions
is 'Allowed curation review states used by curaduria.html: pending, approved, rejected.';

-- 4) Confirm final definition.
select
  conname,
  pg_get_constraintdef(oid) as definition
from pg_constraint
where conrelid = 'public.submissions'::regclass
  and conname = 'submissions_curatorial_review_status_check';

commit;
