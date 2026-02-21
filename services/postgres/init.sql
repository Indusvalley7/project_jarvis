-- Jarvis Control Tower — Database Schema
-- Auto-executed on first Postgres startup

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,          -- Telegram user ID
    username    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Runs
CREATE TABLE IF NOT EXISTS runs (
    run_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     TEXT REFERENCES users(id),
    input_text  TEXT NOT NULL,
    intent      TEXT,
    status      TEXT DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
    reply       TEXT,
    duration_ms DOUBLE PRECISION,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Run Steps
CREATE TABLE IF NOT EXISTS run_steps (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id      UUID REFERENCES runs(run_id) ON DELETE CASCADE,
    step_name   TEXT NOT NULL,
    input_json  JSONB,
    output_json JSONB,
    error       TEXT,
    latency_ms  DOUBLE PRECISION,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Notes
CREATE TABLE IF NOT EXISTS notes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     TEXT REFERENCES users(id),
    content     TEXT NOT NULL,
    tags        TEXT[] DEFAULT '{}',
    qdrant_id   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Reminders
CREATE TABLE IF NOT EXISTS reminders (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     TEXT REFERENCES users(id),
    chat_id     TEXT,
    remind_at   TIMESTAMPTZ NOT NULL,
    message     TEXT NOT NULL,
    status      TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'cancelled')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Workflow Errors
CREATE TABLE IF NOT EXISTS workflow_errors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name   TEXT,
    run_id          UUID REFERENCES runs(run_id) ON DELETE SET NULL,
    error_json      JSONB,
    diagnosis_json  JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_run_steps_run_id ON run_steps(run_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, remind_at) WHERE status = 'scheduled';
CREATE INDEX IF NOT EXISTS idx_workflow_errors_created ON workflow_errors(created_at DESC);
