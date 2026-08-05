PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS state_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_commits (
    state_version INTEGER PRIMARY KEY,
    previous_state_version INTEGER,
    previous_state_sha256 TEXT,
    state_sha256 TEXT NOT NULL UNIQUE,
    logical_export_sha256 TEXT NOT NULL,
    dataset_ref TEXT NOT NULL,
    dataset_version INTEGER NOT NULL,
    git_sha TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    reconciler_run_id TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    committed_at TEXT NOT NULL,
    FOREIGN KEY (previous_state_version) REFERENCES state_commits(state_version)
);

CREATE TABLE IF NOT EXISTS delta_receipts (
    delta_id TEXT PRIMARY KEY,
    delta_sha256 TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    base_state_version INTEGER NOT NULL,
    base_state_sha256 TEXT NOT NULL,
    applied_state_version INTEGER,
    operation_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('reserved','applied','replayed','rejected')),
    rejection_reason TEXT,
    created_at TEXT NOT NULL,
    applied_at TEXT,
    UNIQUE (run_id, stage, delta_sha256)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    trigger_kind TEXT NOT NULL,
    requested_by TEXT,
    git_sha TEXT NOT NULL,
    base_state_version INTEGER NOT NULL,
    result_state_version INTEGER,
    status TEXT NOT NULL CHECK (status IN ('planned','active','complete','failed','blocked','cancelled')),
    started_at TEXT,
    finished_at TEXT,
    run_history_dataset_ref TEXT,
    run_history_dataset_version INTEGER,
    run_bundle_sha256 TEXT,
    github_run_id TEXT,
    summary_json TEXT NOT NULL DEFAULT '{}',
    zero_progress_reason TEXT
);

CREATE TABLE IF NOT EXISTS stage_attempts (
    attempt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'planned','launched','active','terminal_output_pending','output_downloaded',
        'archive_verified','reconciled','complete','failed','blocked','cancelled'
    )),
    worker_ref TEXT,
    worker_version INTEGER,
    auth_scope TEXT,
    base_state_version INTEGER NOT NULL,
    base_state_sha256 TEXT NOT NULL,
    input_sha256 TEXT,
    delta_id TEXT,
    delta_sha256 TEXT,
    output_sha256 TEXT,
    failure_class TEXT,
    failure_reason TEXT,
    started_at TEXT,
    finished_at TEXT,
    heartbeat_at TEXT,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    archive_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (run_id, stage, attempt_no),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_stage_attempts_status ON stage_attempts(status, stage, started_at);
CREATE INDEX IF NOT EXISTS idx_stage_attempts_run ON stage_attempts(run_id, stage);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    canonical_key TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL CHECK (platform IN ('telegram','vk','web','unknown')),
    canonical_url TEXT,
    handle TEXT,
    title TEXT,
    entity_type TEXT,
    geo_class TEXT NOT NULL DEFAULT 'unknown',
    source_type TEXT,
    quality_score REAL,
    status TEXT NOT NULL DEFAULT 'candidate',
    status_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    first_seen_run_id TEXT,
    last_seen_run_id TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status, geo_class, platform);

CREATE TABLE IF NOT EXISTS source_state (
    source_id TEXT PRIMARY KEY,
    last_seen_post_key TEXT,
    last_seen_published_at TEXT,
    last_fetch_at TEXT,
    last_success_at TEXT,
    next_fetch_after TEXT,
    fetch_status TEXT NOT NULL DEFAULT 'pending',
    consecutive_errors INTEGER NOT NULL DEFAULT 0,
    last_error_code TEXT,
    state_revision INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_source_state_due ON source_state(fetch_status, next_fetch_after);

CREATE TABLE IF NOT EXISTS source_profile_evidence (
    evidence_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_url TEXT,
    published_at TEXT,
    observed_at TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    excerpt_sha256 TEXT NOT NULL,
    authored_class TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (source_id, excerpt_sha256),
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_profiles (
    source_profile_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    profile_kind TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','ready','needs_review','insufficient_evidence','blocked')),
    profile_fingerprint TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    model TEXT,
    outlet_identity TEXT,
    intended_audience TEXT,
    distinctive_value TEXT,
    summary TEXT,
    claims_json TEXT NOT NULL DEFAULT '[]',
    evidence_ids_json TEXT NOT NULL DEFAULT '[]',
    conflicts_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    platform_post_key TEXT,
    canonical_url TEXT NOT NULL UNIQUE,
    published_at TEXT,
    fetched_at TEXT,
    text_hash TEXT,
    current_text_version INTEGER,
    has_media INTEGER NOT NULL DEFAULT 0 CHECK (has_media IN (0,1)),
    media_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'candidate',
    terminal_reason TEXT,
    first_seen_run_id TEXT,
    last_seen_run_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (platform, platform_post_key),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
CREATE INDEX IF NOT EXISTS idx_posts_source_date ON posts(source_id, published_at);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status, updated_at);

CREATE TABLE IF NOT EXISTS post_text_versions (
    post_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    text_hash TEXT NOT NULL,
    text_body TEXT,
    language TEXT,
    acquired_at TEXT NOT NULL,
    acquisition_kind TEXT NOT NULL,
    content_facts_json TEXT NOT NULL DEFAULT '[]',
    policy_evidence_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (post_id, version),
    UNIQUE (post_id, text_hash),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS embeddings (
    post_id TEXT NOT NULL,
    model_family TEXT NOT NULL CHECK (model_family IN ('e5','bge','research')),
    model_id TEXT NOT NULL,
    model_revision TEXT NOT NULL,
    encoder_contract TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    semantic_bank_version TEXT NOT NULL,
    vector_dim INTEGER,
    vector_blob BLOB,
    scores_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    run_id TEXT NOT NULL,
    PRIMARY KEY (post_id, model_id, model_revision, text_hash, semantic_bank_version),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_embeddings_missing_pair ON embeddings(model_family, text_hash, created_at);

CREATE TABLE IF NOT EXISTS semantic_matches (
    match_id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    e5_model_revision TEXT NOT NULL,
    bge_model_revision TEXT NOT NULL,
    semantic_bank_version TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','deferred','needs_review')),
    decision_reason TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    run_id TEXT NOT NULL,
    UNIQUE (post_id, text_hash, e5_model_revision, bge_model_revision, semantic_bank_version, policy_version),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_items (
    work_id TEXT PRIMARY KEY,
    queue_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','leased','complete','retry_wait','blocked','cancelled')),
    priority INTEGER NOT NULL DEFAULT 100,
    due_at TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    lease_owner TEXT,
    lease_token TEXT,
    lease_expires_at TEXT,
    input_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    last_error_code TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (queue_name, entity_id, input_fingerprint)
);
CREATE INDEX IF NOT EXISTS idx_work_due ON work_items(queue_name, status, due_at, priority, created_at);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    candidate_revision INTEGER NOT NULL DEFAULT 1,
    current_stage TEXT NOT NULL,
    status TEXT NOT NULL,
    overall_score REAL,
    text_decision TEXT,
    media_decision TEXT,
    profile_status TEXT,
    final_verifier_status TEXT,
    publication_readiness TEXT NOT NULL DEFAULT 'not_ready',
    decision_reason TEXT,
    evidence_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (post_id, evidence_fingerprint),
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
CREATE INDEX IF NOT EXISTS idx_candidates_readiness ON candidates(publication_readiness, status, updated_at);

CREATE TABLE IF NOT EXISTS candidate_decision_events (
    event_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    reason_code TEXT NOT NULL,
    policy_version TEXT,
    evidence_fingerprint TEXT,
    run_id TEXT,
    created_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_candidate_events ON candidate_decision_events(candidate_id, created_at);

CREATE TABLE IF NOT EXISTS media_items (
    media_id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    media_kind TEXT NOT NULL,
    source_ref TEXT,
    refetch_locator_json TEXT NOT NULL DEFAULT '{}',
    reviewed_content_sha256 TEXT,
    ordinal INTEGER,
    width INTEGER,
    height INTEGER,
    duration_seconds REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_media_post ON media_items(post_id, ordinal);

CREATE TABLE IF NOT EXISTS media_decisions (
    media_decision_id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    candidate_id TEXT,
    manifest_fingerprint TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    status TEXT NOT NULL,
    presentation_mode TEXT,
    selected_media_ids_json TEXT NOT NULL DEFAULT '[]',
    scores_json TEXT NOT NULL DEFAULT '{}',
    reason_code TEXT,
    run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (post_id, manifest_fingerprint, contract_version),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS publication_revisions (
    publication_revision_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    revision_no INTEGER NOT NULL,
    operator_review_fingerprint TEXT NOT NULL UNIQUE,
    writer_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    model TEXT,
    source_profile_fingerprint TEXT NOT NULL,
    media_manifest_fingerprint TEXT NOT NULL,
    paragraph_1 TEXT NOT NULL,
    paragraph_2 TEXT NOT NULL,
    source_cta_label TEXT NOT NULL,
    original_url TEXT NOT NULL,
    channel_footer_label TEXT NOT NULL,
    channel_footer_url TEXT NOT NULL,
    visible_char_count INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'draft','needs_grounding_review','ready_for_operator','sent_to_operator',
        'approved','rewrite_requested','rejected','conflict','scheduled','published','superseded'
    )),
    grounding_json TEXT NOT NULL DEFAULT '[]',
    validation_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (candidate_id, revision_no),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pub_revisions_status ON publication_revisions(status, updated_at);

CREATE TABLE IF NOT EXISTS operator_deliveries (
    delivery_id TEXT PRIMARY KEY,
    publication_revision_id TEXT NOT NULL,
    target_chat_id TEXT NOT NULL,
    telegram_message_id TEXT,
    delivery_fingerprint TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('planned','sent','failed','superseded')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    sent_at TEXT,
    last_error TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (publication_revision_id) REFERENCES publication_revisions(publication_revision_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS operator_review_events (
    review_event_id TEXT PRIMARY KEY,
    publication_revision_id TEXT NOT NULL,
    delivery_id TEXT NOT NULL,
    reviewer_id_hash TEXT NOT NULL,
    reaction_kind TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    observation_hash TEXT NOT NULL,
    is_binding INTEGER NOT NULL CHECK (is_binding IN (0,1)),
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (delivery_id, reviewer_id_hash, reaction_kind, observation_hash),
    FOREIGN KEY (publication_revision_id) REFERENCES publication_revisions(publication_revision_id) ON DELETE CASCADE,
    FOREIGN KEY (delivery_id) REFERENCES operator_deliveries(delivery_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS publication_schedule (
    schedule_id TEXT PRIMARY KEY,
    publication_revision_id TEXT NOT NULL,
    content_lane TEXT NOT NULL CHECK (content_lane IN ('article','social')),
    target_platform TEXT NOT NULL CHECK (target_platform IN ('telegram','vk')),
    scheduled_for TEXT NOT NULL,
    slot_key TEXT NOT NULL,
    plan_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned','locked','due','published','cancelled','expired')),
    diversity_json TEXT NOT NULL DEFAULT '{}',
    alternatives_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (target_platform, slot_key),
    FOREIGN KEY (publication_revision_id) REFERENCES publication_revisions(publication_revision_id)
);
CREATE INDEX IF NOT EXISTS idx_schedule_due ON publication_schedule(target_platform, status, scheduled_for);

CREATE TABLE IF NOT EXISTS publication_outbox (
    outbox_id TEXT PRIMARY KEY,
    publication_revision_id TEXT NOT NULL,
    schedule_id TEXT NOT NULL,
    target_platform TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('planned','due','prepared','sending','retry_wait','published','failed_terminal','cancelled')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_after TEXT,
    prepared_payload_sha256 TEXT,
    platform_message_id TEXT,
    platform_url TEXT,
    last_error_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (publication_revision_id) REFERENCES publication_revisions(publication_revision_id),
    FOREIGN KEY (schedule_id) REFERENCES publication_schedule(schedule_id)
);
CREATE INDEX IF NOT EXISTS idx_outbox_due ON publication_outbox(status, next_attempt_after, created_at);

CREATE TABLE IF NOT EXISTS publication_attempts (
    attempt_id TEXT PRIMARY KEY,
    outbox_id TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    platform_message_id TEXT,
    response_sha256 TEXT,
    error_code TEXT,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (outbox_id, attempt_no),
    UNIQUE (request_fingerprint),
    FOREIGN KEY (outbox_id) REFERENCES publication_outbox(outbox_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS provider_request_receipts (
    request_fingerprint TEXT PRIMARY KEY,
    run_id TEXT,
    stage TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    quota_scope_id TEXT,
    status TEXT NOT NULL,
    physical_attempts INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER,
    output_tokens INTEGER,
    reserved_at TEXT,
    sent_at TEXT,
    finalized_at TEXT,
    result_sha256 TEXT,
    error_code TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_provider_stage_time ON provider_request_receipts(stage, finalized_at);

CREATE TABLE IF NOT EXISTS research_imports (
    request_id TEXT PRIMARY KEY,
    input_path TEXT NOT NULL,
    input_sha256 TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('validated','imported','replayed','rejected','conflict')),
    candidate_count INTEGER NOT NULL DEFAULT 0,
    excluded_count INTEGER NOT NULL DEFAULT 0,
    unresolved_count INTEGER NOT NULL DEFAULT 0,
    imported_state_version INTEGER,
    created_at TEXT NOT NULL,
    imported_at TEXT,
    receipt_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS research_identities (
    identity_kind TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    request_id TEXT NOT NULL,
    candidate_external_id TEXT,
    canonical_url TEXT,
    input_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (identity_kind, normalized_value),
    FOREIGN KEY (request_id) REFERENCES research_imports(request_id)
);

CREATE TABLE IF NOT EXISTS research_candidates (
    research_candidate_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    downstream_readiness TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
    publication_permission TEXT NOT NULL DEFAULT 'not_granted',
    source_profile_key TEXT,
    evidence_json TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE (request_id, canonical_url),
    FOREIGN KEY (request_id) REFERENCES research_imports(request_id)
);

CREATE TABLE IF NOT EXISTS product_metric_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    state_version INTEGER NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    metric_version TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    data_quality_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    UNIQUE (state_version, window_start, window_end, metric_version)
);

CREATE TABLE IF NOT EXISTS policy_versions (
    policy_name TEXT NOT NULL,
    version TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft','shadow','active','retired')),
    activated_at TEXT,
    retired_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (policy_name, version)
);

CREATE TABLE IF NOT EXISTS legacy_unmapped_rows (
    source_table TEXT NOT NULL,
    legacy_pk TEXT NOT NULL,
    legacy_kind TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    migration_status TEXT NOT NULL DEFAULT 'unmapped',
    migration_note TEXT,
    imported_at TEXT NOT NULL,
    PRIMARY KEY (source_table, legacy_pk)
);

CREATE TABLE IF NOT EXISTS control_events (
    control_event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

INSERT OR IGNORE INTO schema_migrations(version, name, applied_at, sha256)
VALUES (1, 'initial', strftime('%Y-%m-%dT%H:%M:%fZ','now'), 'BOOTSTRAP_REPLACE_WITH_FILE_SHA256');
