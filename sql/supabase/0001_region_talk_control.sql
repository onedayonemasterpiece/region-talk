-- Minimal Region Talk control/operator projection.
-- Apply to the existing dedicated Google AI limiter project.

begin;

create schema if not exists region_talk_control;
revoke all on schema region_talk_control from public, anon, authenticated;
grant usage on schema region_talk_control to service_role;

create table if not exists region_talk_control.controller_state (
  singleton boolean primary key default true check (singleton),
  mode text not null default 'running' check (mode in ('running','paused','blocked')),
  lease_owner text,
  lease_token uuid,
  lease_expires_at timestamptz,
  latest_tick_at timestamptz,
  latest_success_at timestamptz,
  last_error_code text,
  updated_at timestamptz not null default now()
);
insert into region_talk_control.controller_state(singleton) values (true)
on conflict (singleton) do nothing;

create table if not exists region_talk_control.state_head (
  singleton boolean primary key default true check (singleton),
  dataset_ref text not null,
  dataset_version bigint not null,
  state_sha256 text not null,
  git_sha text not null,
  sqlite_schema_version integer not null,
  committed_at timestamptz not null,
  updated_at timestamptz not null default now()
);

create table if not exists region_talk_control.stage_attempts (
  attempt_id text primary key,
  run_id text not null,
  stage text not null,
  status text not null,
  worker_ref text,
  worker_version bigint,
  auth_scope text,
  base_state_version bigint not null,
  base_state_sha256 text not null,
  heartbeat_at timestamptz,
  started_at timestamptz,
  finished_at timestamptz,
  failure_class text,
  failure_reason text,
  metrics jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  unique (run_id, stage, attempt_id)
);
create index if not exists rt_stage_attempts_active_idx
  on region_talk_control.stage_attempts(status, stage, updated_at desc);

create table if not exists region_talk_control.operator_queue (
  publication_revision_id text primary key,
  candidate_id text not null,
  operator_review_fingerprint text not null unique,
  canonical_url text not null,
  source_label text,
  title text,
  compact_summary text,
  status text not null,
  content_lane text,
  presentation_mode text,
  overall_score double precision,
  scheduled_for timestamptz,
  telegram_message_id bigint,
  last_decision text,
  rewrite_requested boolean not null default false,
  detail_report_ref text,
  updated_at timestamptz not null default now()
);
create index if not exists rt_operator_queue_status_idx
  on region_talk_control.operator_queue(status, scheduled_for, updated_at desc);

create table if not exists region_talk_control.operator_review_events (
  review_event_id text primary key,
  publication_revision_id text not null,
  reviewer_id_hash text not null,
  reaction_kind text not null,
  decision text not null,
  observation_hash text not null,
  observed_at timestamptz not null,
  payload jsonb not null default '{}'::jsonb,
  unique (publication_revision_id, reviewer_id_hash, reaction_kind, observation_hash)
);

create table if not exists region_talk_control.publication_outbox (
  outbox_id text primary key,
  publication_revision_id text not null,
  target_platform text not null,
  idempotency_key text not null unique,
  status text not null,
  scheduled_for timestamptz,
  next_attempt_after timestamptz,
  attempt_count integer not null default 0,
  platform_message_id text,
  platform_url text,
  last_error_code text,
  updated_at timestamptz not null default now()
);
create index if not exists rt_publication_outbox_due_idx
  on region_talk_control.publication_outbox(status, scheduled_for, next_attempt_after);

create table if not exists region_talk_control.control_audit (
  audit_id text primary key,
  event_type text not null,
  actor text not null,
  reason text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists rt_control_audit_time_idx
  on region_talk_control.control_audit(created_at desc);

alter table region_talk_control.controller_state enable row level security;
alter table region_talk_control.state_head enable row level security;
alter table region_talk_control.stage_attempts enable row level security;
alter table region_talk_control.operator_queue enable row level security;
alter table region_talk_control.operator_review_events enable row level security;
alter table region_talk_control.publication_outbox enable row level security;
alter table region_talk_control.control_audit enable row level security;

revoke all on all tables in schema region_talk_control from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema region_talk_control to service_role;

create or replace function region_talk_control.claim_controller(
  p_owner text,
  p_lease_seconds integer default 180
) returns jsonb
language plpgsql
security definer
set search_path = region_talk_control, public
as $$
declare
  v_token uuid := gen_random_uuid();
  v_row region_talk_control.controller_state%rowtype;
begin
  if p_owner is null or length(trim(p_owner)) = 0 then
    raise exception 'owner_required';
  end if;
  if p_lease_seconds < 30 or p_lease_seconds > 900 then
    raise exception 'invalid_lease_seconds';
  end if;

  update region_talk_control.controller_state
     set lease_owner = p_owner,
         lease_token = v_token,
         lease_expires_at = now() + make_interval(secs => p_lease_seconds),
         latest_tick_at = now(),
         updated_at = now()
   where singleton = true
     and mode = 'running'
     and (lease_token is null or lease_expires_at <= now() or lease_owner = p_owner)
  returning * into v_row;

  if not found then
    select * into v_row from region_talk_control.controller_state where singleton = true;
    return jsonb_build_object(
      'ok', false,
      'reason', case when v_row.mode <> 'running' then 'controller_not_running' else 'lease_busy' end,
      'mode', v_row.mode,
      'lease_expires_at', v_row.lease_expires_at
    );
  end if;

  return jsonb_build_object(
    'ok', true,
    'lease_owner', v_row.lease_owner,
    'lease_token', v_row.lease_token,
    'lease_expires_at', v_row.lease_expires_at,
    'mode', v_row.mode
  );
end;
$$;

create or replace function region_talk_control.release_controller(
  p_owner text,
  p_token uuid,
  p_success boolean,
  p_error_code text default null
) returns boolean
language plpgsql
security definer
set search_path = region_talk_control, public
as $$
begin
  update region_talk_control.controller_state
     set lease_owner = null,
         lease_token = null,
         lease_expires_at = null,
         latest_success_at = case when p_success then now() else latest_success_at end,
         last_error_code = case when p_success then null else p_error_code end,
         updated_at = now()
   where singleton = true
     and lease_owner = p_owner
     and lease_token = p_token;
  return found;
end;
$$;

create or replace function region_talk_control.get_snapshot(
  p_operator_limit integer default 50,
  p_attempt_limit integer default 20
) returns jsonb
language sql
security definer
set search_path = region_talk_control, public
stable
as $$
  select jsonb_build_object(
    'controller', (select to_jsonb(c) - 'lease_token' from region_talk_control.controller_state c where singleton),
    'state_head', (select to_jsonb(h) from region_talk_control.state_head h where singleton),
    'active_attempts', coalesce((
      select jsonb_agg(to_jsonb(x) order by x.updated_at desc)
      from (
        select attempt_id, run_id, stage, status, worker_ref, worker_version,
               auth_scope, base_state_version, heartbeat_at, started_at,
               finished_at, failure_class, failure_reason, metrics, updated_at
          from region_talk_control.stage_attempts
         order by updated_at desc
         limit greatest(1, least(p_attempt_limit, 100))
      ) x
    ), '[]'::jsonb),
    'operator_queue', coalesce((
      select jsonb_agg(to_jsonb(q) order by q.updated_at desc)
      from (
        select publication_revision_id, candidate_id, operator_review_fingerprint,
               canonical_url, source_label, title, compact_summary, status,
               content_lane, presentation_mode, overall_score, scheduled_for,
               telegram_message_id, last_decision, rewrite_requested,
               detail_report_ref, updated_at
          from region_talk_control.operator_queue
         order by updated_at desc
         limit greatest(1, least(p_operator_limit, 200))
      ) q
    ), '[]'::jsonb),
    'outbox_due', (select count(*) from region_talk_control.publication_outbox
                    where status in ('due','retry_wait','prepared','sending')
                      and coalesce(next_attempt_after, scheduled_for, now()) <= now())
  );
$$;

create or replace function region_talk_control.compact_hot_history(
  p_before timestamptz,
  p_max_rows integer default 1000
) returns jsonb
language plpgsql
security definer
set search_path = region_talk_control, public
as $$
declare
  v_attempts integer := 0;
  v_audit integer := 0;
begin
  with doomed as (
    select attempt_id from region_talk_control.stage_attempts
     where status in ('complete','failed','blocked','cancelled')
       and updated_at < p_before
     order by updated_at
     limit greatest(1, least(p_max_rows, 5000))
  ) delete from region_talk_control.stage_attempts s using doomed d
    where s.attempt_id = d.attempt_id;
  get diagnostics v_attempts = row_count;

  with doomed as (
    select audit_id from region_talk_control.control_audit
     where created_at < p_before
     order by created_at
     limit greatest(1, least(p_max_rows, 5000))
  ) delete from region_talk_control.control_audit a using doomed d
    where a.audit_id = d.audit_id;
  get diagnostics v_audit = row_count;

  return jsonb_build_object('attempts_deleted', v_attempts, 'audit_deleted', v_audit);
end;
$$;

revoke all on function region_talk_control.claim_controller(text, integer) from public, anon, authenticated;
revoke all on function region_talk_control.release_controller(text, uuid, boolean, text) from public, anon, authenticated;
revoke all on function region_talk_control.get_snapshot(integer, integer) from public, anon, authenticated;
revoke all on function region_talk_control.compact_hot_history(timestamptz, integer) from public, anon, authenticated;
grant execute on function region_talk_control.claim_controller(text, integer) to service_role;
grant execute on function region_talk_control.release_controller(text, uuid, boolean, text) to service_role;
grant execute on function region_talk_control.get_snapshot(integer, integer) to service_role;
grant execute on function region_talk_control.compact_hot_history(timestamptz, integer) to service_role;

commit;
