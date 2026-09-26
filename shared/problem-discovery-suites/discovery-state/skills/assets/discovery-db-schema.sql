-- ============================================================================
-- Canonical SQLite Master Schema for Problem Discovery Lifecycle
-- Hybrid Relational + JSON Document Architecture
-- ============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

-- ----------------------------------------------------------------------------
-- TABLE 1: research_runs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_runs (
    research_id         TEXT PRIMARY KEY,
    original_request    TEXT NOT NULL,
    domain              TEXT NOT NULL,
    scope_type          TEXT DEFAULT 'BROAD',
    geography           TEXT,
    current_stage       TEXT NOT NULL DEFAULT 'PLANNED',
    status              TEXT NOT NULL DEFAULT 'ACTIVE',
    plan_json           TEXT CHECK(plan_json IS NULL OR json_valid(plan_json)),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- TABLE 2: candidates
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id        TEXT PRIMARY KEY,
    research_id         TEXT NOT NULL,
    title               TEXT NOT NULL,
    domain              TEXT NOT NULL,
    target_operator     TEXT,
    track               TEXT DEFAULT 'COMMERCIAL',
    research_score      INTEGER DEFAULT 0 CHECK(research_score BETWEEN 0 AND 35),
    evidence_level      TEXT DEFAULT 'UNASSESSED',
    validation_status   TEXT DEFAULT 'UNVERIFIED',
    lifecycle_status    TEXT DEFAULT 'ACTIVE',
    solution_class      TEXT,
    evaluation_json     TEXT CHECK(evaluation_json IS NULL OR json_valid(evaluation_json)),
    solution_json       TEXT CHECK(solution_json IS NULL OR json_valid(solution_json)),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (research_id) REFERENCES research_runs(research_id)
);

-- ----------------------------------------------------------------------------
-- TABLE 3: evidence_signals
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence_signals (
    signal_id           TEXT PRIMARY KEY,
    research_id         TEXT NOT NULL,
    candidate_id        TEXT,
    stream_id           TEXT,
    platform            TEXT NOT NULL,
    source_url          TEXT,
    actor_role          TEXT,
    reported_issue      TEXT NOT NULL,
    reported_workaround TEXT,
    evidence_level      TEXT NOT NULL DEFAULT 'L3',
    payload_json        TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    retrieved_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (research_id) REFERENCES research_runs(research_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

-- ----------------------------------------------------------------------------
-- TABLE 4: experiments
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id       TEXT PRIMARY KEY,
    candidate_id        TEXT NOT NULL,
    hypothesis          TEXT NOT NULL,
    metric_name         TEXT NOT NULL,
    target_threshold    REAL NOT NULL,
    direction           TEXT NOT NULL DEFAULT '>=',
    sample_target       INTEGER NOT NULL,
    sample_achieved     INTEGER,
    observed_value      REAL,
    outcome_verdict     TEXT DEFAULT 'NOT_RUN',
    contract_json       TEXT CHECK(contract_json IS NULL OR json_valid(contract_json)),
    assessment_json     TEXT CHECK(assessment_json IS NULL OR json_valid(assessment_json)),
    artifact_hash       TEXT,
    audited_by          TEXT,
    audit_date          DATE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

-- ----------------------------------------------------------------------------
-- FULL-TEXT SEARCH VIRTUAL INDEX
-- ----------------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS discovery_fts USING fts5(
    entity_id,
    entity_type,
    title_or_issue,
    body_text
);

-- ----------------------------------------------------------------------------
-- INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_signals_research_id ON evidence_signals(research_id);
CREATE INDEX IF NOT EXISTS idx_signals_candidate_id ON evidence_signals(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_research_id ON candidates(research_id);
CREATE INDEX IF NOT EXISTS idx_candidates_lifecycle ON candidates(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_experiments_candidate_id ON experiments(candidate_id);

-- ----------------------------------------------------------------------------
-- MASTER DECISION DASHBOARD VIEW
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_discovery_dashboard AS
SELECT 
    c.candidate_id,
    c.title,
    c.domain,
    c.target_operator,
    c.track,
    c.research_score,
    c.evidence_level,
    c.validation_status,
    c.solution_class,
    c.lifecycle_status,
    COUNT(DISTINCT s.signal_id) AS total_evidence_count,
    COALESCE(MAX(e.outcome_verdict), 'NOT_RUN') AS latest_experiment_verdict,
    c.updated_at
FROM candidates c
LEFT JOIN evidence_signals s ON c.candidate_id = s.candidate_id
LEFT JOIN experiments e ON c.candidate_id = e.candidate_id
GROUP BY c.candidate_id;
