-- Take It Down Backend Database Schema
-- PostgreSQL-compatible with audit logging and lineage tracking

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table with role-based access control
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('victim', 'officer', 'admin')),
    jurisdiction VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Cases table with lineage tracking
CREATE TABLE cases (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_ref VARCHAR(20) UNIQUE NOT NULL, -- e.g., CASE-2025-0001
    submitter_id UUID NOT NULL REFERENCES users(user_id),
    assigned_officer_id UUID REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Submitted', 'In Review', 'Approved', 'Rejected', 'Escalated', 'Closed')),
    jurisdiction VARCHAR(10) NOT NULL,
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    
    -- Lineage tracking for duplicate detection
    origin_case_id UUID REFERENCES cases(case_id),
    lineage_depth INTEGER DEFAULT 0,
    
    -- SLA tracking
    sla_due_at TIMESTAMP WITH TIME ZONE,
    sla_violated BOOLEAN DEFAULT false,
    escalation_level INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    policy_version VARCHAR(20) DEFAULT 'redaction_policy_v1.0',
    notes TEXT,
    
    -- Indexes
    CONSTRAINT cases_submitter_fk FOREIGN KEY (submitter_id) REFERENCES users(user_id),
    CONSTRAINT cases_officer_fk FOREIGN KEY (assigned_officer_id) REFERENCES users(user_id)
);

-- Submissions table (individual URLs/hashes per case)
CREATE TABLE submissions (
    submission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    kind VARCHAR(10) NOT NULL CHECK (kind IN ('URL', 'HASH')),
    content TEXT NOT NULL,
    
    -- Deduplication
    normalized_content TEXT NOT NULL,
    dedup_hash VARCHAR(64) NOT NULL, -- SHA256 hash
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Indexes for fast dedup lookups
    UNIQUE(case_id, dedup_hash)
);

-- Comprehensive audit logs with reason codes
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(case_id),
    actor_id UUID REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,
    old_state TEXT,
    new_state TEXT,
    reason_code VARCHAR(50), -- e.g., 'jurisdiction_issue', 'duplicate_case'
    
    -- Rich metadata
    meta JSONB,
    ip_address INET,
    user_agent TEXT,
    
    -- Tamper-proofing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    checksum VARCHAR(64) -- For integrity verification
);

-- SLA timers for escalation tracking
CREATE TABLE sla_timers (
    timer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    timer_type VARCHAR(20) NOT NULL CHECK (timer_type IN ('review', 'escalation', 'resolution')),
    due_at TIMESTAMP WITH TIME ZONE NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'triggered', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Reports table for compliance exports
CREATE TABLE reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(case_id),
    generated_by UUID NOT NULL REFERENCES users(user_id),
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('audit', 'sla', 'compliance', 'export')),
    format VARCHAR(10) NOT NULL CHECK (format IN ('csv', 'json', 'pdf')),
    file_path TEXT,
    file_size_bytes BIGINT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Notifications table
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(case_id),
    recipient_id UUID NOT NULL REFERENCES users(user_id),
    notification_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(10) DEFAULT 'info' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- System configuration
CREATE TABLE system_config (
    config_key VARCHAR(50) PRIMARY KEY,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_by UUID REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_submitter ON cases(submitter_id);
CREATE INDEX idx_cases_officer ON cases(assigned_officer_id);
CREATE INDEX idx_cases_sla_due ON cases(sla_due_at) WHERE status = 'In Review';
CREATE INDEX idx_cases_lineage ON cases(origin_case_id);

CREATE INDEX idx_submissions_dedup ON submissions(dedup_hash);
CREATE INDEX idx_submissions_case ON submissions(case_id);

CREATE INDEX idx_audit_case ON audit_logs(case_id);
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

CREATE INDEX idx_sla_timers_due ON sla_timers(due_at) WHERE status = 'pending';
CREATE INDEX idx_sla_timers_case ON sla_timers(case_id);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_status ON notifications(status);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate case reference
CREATE OR REPLACE FUNCTION generate_case_ref()
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    sequence_num INTEGER;
    case_ref TEXT;
BEGIN
    year_part := EXTRACT(YEAR FROM now())::TEXT;
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(case_ref FROM 'CASE-' || year_part || '-(.+)') AS INTEGER)), 0) + 1
    INTO sequence_num
    FROM cases
    WHERE case_ref LIKE 'CASE-' || year_part || '-%';
    
    case_ref := 'CASE-' || year_part || '-' || LPAD(sequence_num::TEXT, 4, '0');
    RETURN case_ref;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate audit log checksum
CREATE OR REPLACE FUNCTION calculate_audit_checksum(
    p_log_id UUID,
    p_case_id UUID,
    p_actor_id UUID,
    p_action VARCHAR,
    p_old_state TEXT,
    p_new_state TEXT,
    p_created_at TIMESTAMP WITH TIME ZONE
)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(
        digest(
            p_log_id::TEXT || p_case_id::TEXT || p_actor_id::TEXT || 
            p_action || COALESCE(p_old_state, '') || COALESCE(p_new_state, '') || 
            p_created_at::TEXT,
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql;

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('redaction_policy_version', 'redaction_policy_v1.0', 'Current redaction policy version'),
('review_sla_hours', '48', 'SLA hours for case review'),
('escalation_grace_hours', '2', 'Grace period before escalation'),
('max_escalation_levels', '3', 'Maximum escalation levels'),
('notification_retry_attempts', '3', 'Number of notification retry attempts'),
('audit_retention_days', '2555', 'Audit log retention period (7 years)');

-- Create views for common queries
CREATE VIEW case_summary AS
SELECT 
    c.case_id,
    c.case_ref,
    c.status,
    c.priority,
    c.jurisdiction,
    c.created_at,
    c.sla_due_at,
    c.sla_violated,
    c.escalation_level,
    u.username as submitter_name,
    u2.username as assigned_officer_name,
    COUNT(s.submission_id) as submission_count,
    CASE 
        WHEN c.sla_due_at < now() AND c.status = 'In Review' THEN 'overdue'
        WHEN c.sla_due_at < now() + INTERVAL '2 hours' AND c.status = 'In Review' THEN 'near_due'
        ELSE 'on_time'
    END as sla_status
FROM cases c
LEFT JOIN users u ON c.submitter_id = u.user_id
LEFT JOIN users u2 ON c.assigned_officer_id = u2.user_id
LEFT JOIN submissions s ON c.case_id = s.case_id
GROUP BY c.case_id, c.case_ref, c.status, c.priority, c.jurisdiction, 
         c.created_at, c.sla_due_at, c.sla_violated, c.escalation_level,
         u.username, u2.username;

-- Create view for SLA compliance metrics
CREATE VIEW sla_metrics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    jurisdiction,
    COUNT(*) as total_cases,
    COUNT(*) FILTER (WHERE status = 'Approved' AND sla_violated = false) as resolved_on_time,
    COUNT(*) FILTER (WHERE sla_violated = true) as sla_violations,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'Approved' AND sla_violated = false) / 
        NULLIF(COUNT(*) FILTER (WHERE status IN ('Approved', 'Rejected')), 0), 
        2
    ) as compliance_percentage
FROM cases
WHERE created_at >= now() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at), jurisdiction
ORDER BY date DESC;
