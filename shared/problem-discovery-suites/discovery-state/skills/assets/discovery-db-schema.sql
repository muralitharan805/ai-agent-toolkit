-- ============================================================================
-- Canonical SQLite Master Schema for Problem Discovery Lifecycle
-- Hybrid Relational + JSON Document Architecture
-- discovery-state is the ONLY schema authority.
-- ============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS research_runs (
    research_id         TEXT PRIMARY KEY,
    original_request    TEXT NOT NULL,
    domain              TEXT NOT NULL,
    scope_type          TEXT NOT NULL DEFAULT 'BROAD',
    geography           TEXT,
    current_stage       TEXT NOT NULL DEFAULT 'RESEARCH_PLANNING',
    status              TEXT NOT NULL DEFAULT 'ACTIVE',
    plan_json           TEXT CHECK(plan_json IS NULL OR json_valid(plan_json)),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id        TEXT PRIMARY KEY,
    origin_research_id  TEXT NOT NULL,
    title               TEXT NOT NULL,
    domain              TEXT NOT NULL,
    target_operator     TEXT,
    track               TEXT NOT NULL DEFAULT 'COMMERCIAL',
    research_score      INTEGER CHECK(research_score IS NULL OR research_score BETWEEN 0 AND 35),
    evidence_level      TEXT NOT NULL DEFAULT 'UNASSESSED'
                        CHECK(evidence_level IN ('UNASSESSED','L1','L2','L3','L4','L5')),
    validation_status   TEXT NOT NULL DEFAULT 'UNVERIFIED'
                        CHECK(validation_status IN ('UNVERIFIED','IN_PROGRESS','PARTIALLY_VALIDATED','VALIDATED')),
    lifecycle_status    TEXT NOT NULL DEFAULT 'ACTIVE',
    solution_class      TEXT,
    evaluation_json     TEXT CHECK(evaluation_json IS NULL OR json_valid(evaluation_json)),
    solution_json       TEXT CHECK(solution_json IS NULL OR json_valid(solution_json)),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (origin_research_id) REFERENCES research_runs(research_id)
);

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
    evidence_level      TEXT NOT NULL DEFAULT 'UNASSESSED'
                        CHECK(evidence_level IN ('UNASSESSED','L1','L2','L3','L4','L5')),
    payload_json        TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    retrieved_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (research_id) REFERENCES research_runs(research_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id       TEXT PRIMARY KEY,
    candidate_id        TEXT NOT NULL,
    hypothesis          TEXT NOT NULL,
    metric_name         TEXT NOT NULL,
    target_threshold    REAL NOT NULL,
    direction           TEXT NOT NULL DEFAULT '>=',
    sample_target       INTEGER NOT NULL CHECK(sample_target > 0),
    sample_achieved     INTEGER,
    observed_value      REAL,
    outcome_verdict     TEXT NOT NULL DEFAULT 'PREREGISTERED'
                        CHECK(outcome_verdict IN ('PREREGISTERED','PASSED','FAILED','INCOMPLETE','INVALID','CANCELLED')),
    contract_json       TEXT NOT NULL CHECK(json_valid(contract_json)),
    assessment_json     TEXT CHECK(assessment_json IS NULL OR json_valid(assessment_json)),
    artifact_hash       TEXT,
    audited_by          TEXT,
    audit_date          DATE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS discovery_fts USING fts5(
    entity_id,
    entity_type,
    title_or_issue,
    body_text
);

CREATE INDEX IF NOT EXISTS idx_signals_research_id ON evidence_signals(research_id);
CREATE INDEX IF NOT EXISTS idx_signals_candidate_id ON evidence_signals(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_origin_research_id ON candidates(origin_research_id);
CREATE INDEX IF NOT EXISTS idx_candidates_domain ON candidates(domain);
CREATE INDEX IF NOT EXISTS idx_candidates_lifecycle ON candidates(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_experiments_candidate_id ON experiments(candidate_id);

DROP VIEW IF EXISTS v_discovery_dashboard;
CREATE VIEW v_discovery_dashboard AS
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
    COUNT(DISTINCT s.research_id) AS research_run_count,
    (SELECT COUNT(*) FROM experiments e WHERE e.candidate_id = c.candidate_id) AS experiment_count,
    (SELECT COUNT(*) FROM experiments e WHERE e.candidate_id = c.candidate_id AND e.outcome_verdict = 'PASSED') AS passed_experiments,
    (SELECT COUNT(*) FROM experiments e WHERE e.candidate_id = c.candidate_id AND e.outcome_verdict = 'FAILED') AS failed_experiments,
    (SELECT COUNT(*) FROM experiments e WHERE e.candidate_id = c.candidate_id AND e.outcome_verdict = 'INVALID') AS invalid_experiments,
    (SELECT COUNT(*) FROM experiments e WHERE e.candidate_id = c.candidate_id AND e.outcome_verdict = 'INCOMPLETE') AS incomplete_experiments,
    COALESCE(
        (
            SELECT e2.outcome_verdict
            FROM experiments e2
            WHERE e2.candidate_id = c.candidate_id
            ORDER BY e2.created_at DESC, e2.experiment_id DESC
            LIMIT 1
        ),
        'NOT_RUN'
    ) AS latest_experiment_verdict,
    c.updated_at
FROM candidates c
LEFT JOIN evidence_signals s ON c.candidate_id = s.candidate_id
GROUP BY c.candidate_id;
