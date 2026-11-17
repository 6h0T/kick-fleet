CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'kick',
    credential_blob BYTEA NOT NULL,
    status TEXT NOT NULL DEFAULT 'provisioning',
    health_score INTEGER NOT NULL DEFAULT 100,
    last_login_at TIMESTAMPTZ,
    assigned_worker_id TEXT,
    profile_key TEXT,
    notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, username)
);

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    worker_id TEXT,
    status TEXT NOT NULL DEFAULT 'starting',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    storage_state_blob BYTEA,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS workers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'starting',
    cpu_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
    ram_mb DOUBLE PRECISION NOT NULL DEFAULT 0,
    ram_limit_mb DOUBLE PRECISION,
    novnc_url TEXT,
    vnc_port INTEGER,
    last_heartbeat_at TIMESTAMPTZ,
    labels JSONB NOT NULL DEFAULT '{}'::jsonb,
    snapshot_jpeg BYTEA,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    worker_id TEXT,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB,
    error TEXT,
    run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    worker_id TEXT,
    channel TEXT NOT NULL,
    direction TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS interaction_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL DEFAULT 'kick',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    steps JSONB NOT NULL,
    trigger JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS event_logs (
    id BIGSERIAL PRIMARY KEY,
    worker_id TEXT,
    level TEXT NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    extra JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status_run_at ON tasks (status, run_at);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_created ON event_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_account ON sessions (account_id);

INSERT INTO interaction_scripts (name, platform, enabled, steps, trigger)
VALUES
(
    'kick-open-channel',
    'kick',
    TRUE,
    '[
        {"action": "goto_channel", "channel": "{{channel}}"},
        {"action": "wait_chat", "timeout_ms": 20000}
    ]'::jsonb,
    NULL
),
(
    'kick-authorized-test-message',
    'kick',
    TRUE,
    '[
        {"action": "goto_channel", "channel": "{{channel}}"},
        {"action": "wait_chat", "timeout_ms": 20000},
        {"action": "send_chat", "text": "{{text}}"},
        {"action": "listen", "duration_ms": 15000}
    ]'::jsonb,
    NULL
)
ON CONFLICT (name) DO NOTHING;
