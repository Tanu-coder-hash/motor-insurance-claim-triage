
CREATE TABLE IF NOT EXISTS runs (
    run_id UUID PRIMARY KEY,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    correlation_id VARCHAR(100),
    fnol_data JSONB NOT NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS run_steps (
    run_id UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (run_id, seq)
);

CREATE TABLE IF NOT EXISTS quarantine (
    quarantine_id UUID PRIMARY KEY,
    raw_request TEXT NOT NULL,
    validation_errors JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(run_id),
    rating INTEGER,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS live_scores (
    score_id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES runs(run_id),
    model_name VARCHAR(100),
    score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS index_manifest (
    manifest_id BIGSERIAL PRIMARY KEY,
    index_version VARCHAR(100) NOT NULL,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_status
ON runs(status);

CREATE INDEX IF NOT EXISTS idx_runs_created_at
ON runs(created_at);

CREATE INDEX IF NOT EXISTS idx_run_steps_run_id
ON run_steps(run_id);

CREATE INDEX IF NOT EXISTS idx_feedback_run_id
ON feedback(run_id);
