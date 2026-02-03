-- WhatsApp Form Auto-Fill System Database Schema
-- SQLite Database for logging, pattern learning, and state management

-- ============================================
-- FORM SUBMISSIONS LOG
-- ============================================
CREATE TABLE IF NOT EXISTS form_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Form Details
    form_url TEXT NOT NULL,
    form_provider TEXT NOT NULL, -- 'microsoft_forms', 'google_forms', etc.
    form_signature TEXT, -- Hash of DOM structure for pattern matching
    
    -- Processing Details
    detection_method TEXT NOT NULL, -- 'rule_based', 'ai_assisted', 'learned_pattern'
    confidence_score REAL,
    
    -- User Data Submitted
    student_name TEXT,
    student_id TEXT,
    
    -- Submission Result
    status TEXT NOT NULL, -- 'success', 'failed', 'captcha', 'skipped'
    error_message TEXT,
    
    -- Screenshots & Evidence
    screenshot_before TEXT,
    screenshot_filled TEXT,
    screenshot_after TEXT,
    dom_snapshot TEXT,
    
    -- Timing
    processing_time_seconds REAL,
    
    -- Metadata
    whatsapp_message TEXT,
    user_agent TEXT
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_submissions_timestamp ON form_submissions(timestamp);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON form_submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_signature ON form_submissions(form_signature);

-- ============================================
-- LEARNED FIELD PATTERNS
-- ============================================
CREATE TABLE IF NOT EXISTS field_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Form Identification
    form_signature TEXT UNIQUE NOT NULL,
    form_provider TEXT NOT NULL,
    
    -- Field Mappings (JSON)
    field_mappings TEXT NOT NULL, -- JSON: {"name": "selector", "student_id": "selector", ...}
    
    -- Success Tracking
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used_at DATETIME,
    
    -- Confidence
    pattern_confidence REAL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_patterns_signature ON field_patterns(form_signature);
CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON field_patterns(pattern_confidence);

-- ============================================
-- ERROR LOG
-- ============================================
CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Error Details
    error_type TEXT NOT NULL, -- 'captcha', 'network', 'parsing', 'automation', etc.
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    
    -- Context
    form_url TEXT,
    agent_name TEXT,
    
    -- Recovery
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_successful BOOLEAN DEFAULT FALSE,
    
    -- Screenshot
    screenshot_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON error_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_errors_type ON error_log(error_type);

-- ============================================
-- WHATSAPP SESSION MANAGEMENT
-- ============================================
CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Session Data
    session_data TEXT, -- Serialized cookies/localStorage
    phone_number TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    qr_scan_required BOOLEAN DEFAULT FALSE
);

-- ============================================
-- MESSAGE QUEUE
-- ============================================
CREATE TABLE IF NOT EXISTS message_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    
    -- Message Details
    message_text TEXT NOT NULL,
    form_url TEXT NOT NULL,
    group_name TEXT,
    
    -- Processing Status
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    attempts INTEGER DEFAULT 0,
    
    -- Result
    submission_id INTEGER,
    FOREIGN KEY (submission_id) REFERENCES form_submissions(id)
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON message_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_created ON message_queue(created_at);

-- ============================================
-- SYSTEM STATS
-- ============================================
CREATE TABLE IF NOT EXISTS system_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    
    -- Daily Counts
    total_forms_processed INTEGER DEFAULT 0,
    successful_submissions INTEGER DEFAULT 0,
    failed_submissions INTEGER DEFAULT 0,
    captcha_triggered INTEGER DEFAULT 0,
    
    -- Performance
    avg_processing_time_seconds REAL DEFAULT 0.0,
    
    -- AI Usage
    ai_fallback_used INTEGER DEFAULT 0,
    rule_based_success INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_stats_date ON system_stats(date);

-- ============================================
-- INITIAL DATA
-- ============================================
INSERT OR IGNORE INTO system_stats (date, total_forms_processed)
VALUES (DATE('now'), 0);
