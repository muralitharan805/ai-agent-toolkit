# Database Schema & DDL Reference

## Purpose
This document provides the authoritative Data Definition Language (DDL) specification for the SQLite persistence store in the modular problem discovery ecosystem. The architecture implements a **Hybrid Relational + JSON Document Model** with WAL mode and strict foreign key integrity.

---

## Master SQLite DDL Specification

```sql
-- ============================================================================
-- PRAGMAS & ENVIRONMENT SETUP
-- ============================================================================
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

-- ============================================================================
-- TABLE 1: research_runs
-- Root entity representing an exploratory intent or problem domain investigation.
-- ============================================================================
CREATE TABLE IF NOT EXISTS research_runs (
    research_id         TEXT PRIMARY KEY,                  -- e.g. 'run_2026_001'
    original_request    TEXT NOT NULL,                     -- Raw user input / prompt
    domain              TEXT NOT NULL,                     -- e.g. 'ecommerce_logistics'
    scope_type          TEXT DEFAULT 'BROAD',              -- 'BROAD', 'NARROW', 'MESSY_BRAINDUMP'
    geography           TEXT,                              -- Target region or NULL
    current_stage       TEXT NOT NULL DEFAULT 'PLANNED',   -- 'PLANNED', 'RESEARCHED', 'EVALUATED', 'COMPLETED'
    status              TEXT NOT NULL DEFAULT 'ACTIVE',    -- 'ACTIVE', 'COMPLETED', 'ARCHIVED'
    plan_json           TEXT CHECK(plan_json IS NULL OR json_valid(plan_json)),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 2: candidates
-- Specific evaluated problem candidates formed from clusters of evidence signals.
-- ============================================================================
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id        TEXT PRIMARY KEY,                  -- e.g. 'cand_courier_disputes'
    research_id         TEXT NOT NULL,                     -- Foreign Key to research_runs
    title               TEXT NOT NULL,                     -- Problem candidate title
    domain              TEXT NOT NULL,
    target_operator     TEXT,                              -- Specific human operator persona
    track               TEXT DEFAULT 'COMMERCIAL',         -- 'COMMERCIAL' | 'FREE_UTILITY'
    
    -- Scoring & Status Gates
    research_score      INTEGER DEFAULT 0 CHECK(research_score BETWEEN 0 AND 35),
    evidence_level      TEXT DEFAULT 'UNASSESSED',         -- 'L1', 'L2', 'L3', 'L4', 'L5'
    validation_status   TEXT DEFAULT 'UNVERIFIED',         -- 'UNVERIFIED', 'VALIDATED', 'EXPERIMENT_FAILED'
    lifecycle_status    TEXT DEFAULT 'ACTIVE',             -- 'ACTIVE', 'RESEARCH_PRIORITY', 'PARKED', 'ARCHIVED', 'READY_TO_BUILD'
    solution_class      TEXT,                              -- Selected from 17 solution classes
    
    -- Document Snapshots
    evaluation_json     TEXT CHECK(evaluation_json IS NULL OR json_valid(evaluation_json)),
    solution_json       TEXT CHECK(solution_json IS NULL OR json_valid(solution_json)),
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (research_id) REFERENCES research_runs(research_id)
);

-- ============================================================================
-- TABLE 3: evidence_signals
-- Empirical observations gathered from primary online sources or interviews.
-- ============================================================================
CREATE TABLE IF NOT EXISTS evidence_signals (
    signal_id           TEXT PRIMARY KEY,                  -- e.g. 'sig_reddit_001'
    research_id         TEXT NOT NULL,                     -- Mandatory FK to research_runs
    candidate_id        TEXT,                              -- Nullable FK! Linked during problem evaluation
    stream_id           TEXT,                              -- Research stream ID e.g. 'RS-001'
    platform            TEXT NOT NULL,                     -- 'REDDIT', 'HACKERNEWS', 'GITHUB', 'FORUM', 'INTERVIEW'
    source_url          TEXT,                              -- Permanent source permalink
    actor_role          TEXT,                              -- Self-reported role of complainer
    reported_issue      TEXT NOT NULL,                     -- Verbatim operational complaint
    reported_workaround TEXT,                              -- Existing glue work (Excel, manual)
    evidence_level      TEXT NOT NULL DEFAULT 'L3',        -- 'L1' to 'L5'
    payload_json        TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    retrieved_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (research_id) REFERENCES research_runs(research_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

-- ============================================================================
-- TABLE 4: experiments
-- Preregistered empirical trials and verified outcome assessments.
-- ============================================================================
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id       TEXT PRIMARY KEY,                  -- e.g. 'exp_weight_audit_001'
    candidate_id        TEXT NOT NULL,                     -- FK to candidates
    hypothesis          TEXT NOT NULL,                     -- Falsifiable claim
    metric_name         TEXT NOT NULL,                     -- e.g. 'dispute_csv_submissions'
    target_threshold    REAL NOT NULL,                     -- Numeric target threshold (e.g. 3.0)
    direction           TEXT NOT NULL DEFAULT '>=',        -- '>=' or '<='
    sample_target       INTEGER NOT NULL,                  -- Target sample size (e.g. 10)
    sample_achieved     INTEGER,
    observed_value      REAL,
    outcome_verdict     TEXT DEFAULT 'NOT_RUN',            -- 'VALIDATED', 'EXPERIMENT_FAILED', 'INCOMPLETE'
    
    -- Contracts & Proofs
    contract_json       TEXT CHECK(contract_json IS NULL OR json_valid(contract_json)),
    assessment_json     TEXT CHECK(assessment_json IS NULL OR json_valid(assessment_json)),
    artifact_hash       TEXT,                              -- SHA-256 byte digest of evidence proof
    audited_by          TEXT,                              -- Verified reviewer name
    audit_date          DATE,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

-- ============================================================================
-- FULL-TEXT SEARCH VIRTUAL INDEX (discovery_fts)
-- ============================================================================
CREATE VIRTUAL TABLE IF NOT EXISTS discovery_fts USING fts5(
    entity_id,
    entity_type,                                           -- 'RUN', 'CANDIDATE', 'SIGNAL'
    title_or_issue,
    body_text
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_signals_research_id ON evidence_signals(research_id);
CREATE INDEX IF NOT EXISTS idx_signals_candidate_id ON evidence_signals(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_research_id ON candidates(research_id);
CREATE INDEX IF NOT EXISTS idx_candidates_lifecycle ON candidates(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_experiments_candidate_id ON experiments(candidate_id);

-- ============================================================================
-- MASTER DECISION DASHBOARD VIEW
-- Flattened canonical decision view eliminating multi-table joins for callers.
-- ============================================================================
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
```
