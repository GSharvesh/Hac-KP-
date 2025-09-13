-- Take It Down Backend - Sample Data Seeding
-- Safe test data for demo purposes

-- Insert sample users
INSERT INTO users (user_id, username, email, role, jurisdiction, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'victim_jane_doe', 'jane.doe@example.com', 'victim', 'IN', true),
('550e8400-e29b-41d4-a716-446655440002', 'victim_john_smith', 'john.smith@example.com', 'victim', 'US', true),
('550e8400-e29b-41d4-a716-446655440003', 'officer_alex_brown', 'alex.brown@law.gov', 'officer', 'IN', true),
('550e8400-e29b-41d4-a716-446655440004', 'officer_sarah_wilson', 'sarah.wilson@law.gov', 'officer', 'US', true),
('550e8400-e29b-41d4-a716-446655440005', 'admin_mike_chen', 'mike.chen@admin.gov', 'admin', 'GLOBAL', true);

-- Insert sample cases
INSERT INTO cases (case_id, case_ref, submitter_id, assigned_officer_id, status, jurisdiction, priority, sla_due_at, sla_violated, escalation_level, policy_version, notes) VALUES
('650e8400-e29b-41d4-a716-446655440001', 'CASE-2025-0001', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'Submitted', 'IN', 'medium', now() + INTERVAL '48 hours', false, 0, 'redaction_policy_v1.0', 'Initial submission from victim'),
('650e8400-e29b-41d4-a716-446655440002', 'CASE-2025-0002', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440004', 'In Review', 'US', 'high', now() + INTERVAL '24 hours', false, 0, 'redaction_policy_v1.0', 'High priority case under review'),
('650e8400-e29b-41d4-a716-446655440003', 'CASE-2025-0003', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'Approved', 'IN', 'medium', now() - INTERVAL '2 hours', false, 0, 'redaction_policy_v1.0', 'Successfully approved case'),
('650e8400-e29b-41d4-a716-446655440004', 'CASE-2025-0004', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440004', 'Escalated', 'US', 'urgent', now() - INTERVAL '72 hours', true, 2, 'redaction_policy_v1.0', 'Escalated due to SLA violation'),
('650e8400-e29b-41d4-a716-446655440005', 'CASE-2025-0005', '550e8400-e29b-41d4-a716-446655440001', NULL, 'Submitted', 'IN', 'low', now() + INTERVAL '48 hours', false, 0, 'redaction_policy_v1.0', 'Duplicate case - linked to origin');

-- Update case 5 to show lineage tracking
UPDATE cases SET origin_case_id = '650e8400-e29b-41d4-a716-446655440001', lineage_depth = 1 WHERE case_id = '650e8400-e29b-41d4-a716-446655440005';

-- Insert sample submissions
INSERT INTO submissions (case_id, kind, content, normalized_content, dedup_hash) VALUES
-- Case 1 submissions
('650e8400-e29b-41d4-a716-446655440001', 'URL', 'https://fake-report.com/content123', 'https://fake-report.com/content123', 'sha256_normalized_url_hash_001'),
('650e8400-e29b-41d4-a716-446655440001', 'URL', 'https://harmful-demo.example.com/badcontent', 'https://harmful-demo.example.com/badcontent', 'sha256_normalized_url_hash_002'),

-- Case 2 submissions  
('650e8400-e29b-41d4-a716-446655440002', 'HASH', '1234abcd5678efgh91011ijklmnopqrstuvwx1234abcd5678efgh91011ijklmnop', '1234abcd5678efgh91011ijklmnopqrstuvwx1234abcd5678efgh91011ijklmnop', '1234abcd5678efgh91011ijklmnopqrstuvwx1234abcd5678efgh91011ijklmnop'),

-- Case 3 submissions
('650e8400-e29b-41d4-a716-446655440003', 'URL', 'https://demo-case.org/abc456', 'https://demo-case.org/abc456', 'sha256_normalized_url_hash_003'),

-- Case 4 submissions
('650e8400-e29b-41d4-a716-446655440004', 'HASH', '9876zyxw5432vuts1098rqpo7654nmlkjihgfedcba9876zyxw5432vuts1098rqpo', '9876zyxw5432vuts1098rqpo7654nmlkjihgfedcba9876zyxw5432vuts1098rqpo', '9876zyxw5432vuts1098rqpo7654nmlkjihgfedcba9876zyxw5432vuts1098rqpo'),

-- Case 5 submissions (duplicate of case 1)
('650e8400-e29b-41d4-a716-446655440005', 'URL', 'https://fake-report.com/content123', 'https://fake-report.com/content123', 'sha256_normalized_url_hash_001');

-- Insert sample audit logs
INSERT INTO audit_logs (log_id, case_id, actor_id, action, old_state, new_state, reason_code, meta, ip_address, user_agent, created_at) VALUES
-- Case 1 logs
('750e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'case_created', NULL, 'Submitted', 'initial_submission', '{"submission_count": 2, "jurisdiction": "IN"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', now() - INTERVAL '2 hours'),
('750e8400-e29b-41d4-a716-446655440002', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'review_started', 'Submitted', 'In Review', 'officer_assignment', '{"assigned_officer": "officer_alex_brown"}', '192.168.1.200', 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36', now() - INTERVAL '1 hour'),

-- Case 2 logs
('750e8400-e29b-41d4-a716-446655440003', '650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'case_created', NULL, 'Submitted', 'initial_submission', '{"submission_count": 1, "jurisdiction": "US", "priority": "high"}', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', now() - INTERVAL '3 hours'),
('750e8400-e29b-41d4-a716-446655440004', '650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440004', 'review_started', 'Submitted', 'In Review', 'officer_assignment', '{"assigned_officer": "officer_sarah_wilson"}', '192.168.1.201', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', now() - INTERVAL '2 hours'),

-- Case 3 logs
('750e8400-e29b-41d4-a716-446655440005', '650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'case_created', NULL, 'Submitted', 'initial_submission', '{"submission_count": 1, "jurisdiction": "IN"}', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', now() - INTERVAL '4 hours'),
('750e8400-e29b-41d4-a716-446655440006', '650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'review_started', 'Submitted', 'In Review', 'officer_assignment', '{"assigned_officer": "officer_alex_brown"}', '192.168.1.202', 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36', now() - INTERVAL '3 hours'),
('750e8400-e29b-41d4-a716-446655440007', '650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'case_approved', 'In Review', 'Approved', 'content_verified_harmful', '{"review_duration_minutes": 30, "verification_method": "automated_scan"}', '192.168.1.202', 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36', now() - INTERVAL '2 hours'),

-- Case 4 logs
('750e8400-e29b-41d4-a716-446655440008', '650e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 'case_created', NULL, 'Submitted', 'initial_submission', '{"submission_count": 1, "jurisdiction": "US", "priority": "urgent"}', '192.168.1.103', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', now() - INTERVAL '72 hours'),
('750e8400-e29b-41d4-a716-446655440009', '650e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440004', 'review_started', 'Submitted', 'In Review', 'officer_assignment', '{"assigned_officer": "officer_sarah_wilson"}', '192.168.1.203', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', now() - INTERVAL '70 hours'),
('750e8400-e29b-41d4-a716-446655440010', '650e8400-e29b-41d4-a716-446655440004', 'system', 'case_escalated', 'In Review', 'Escalated', 'sla_violation', '{"sla_hours_overdue": 24, "escalation_level": 1}', '192.168.1.1', 'System/1.0', now() - INTERVAL '24 hours'),
('750e8400-e29b-41d4-a716-446655440011', '650e8400-e29b-41d4-a716-446655440004', 'system', 'case_escalated', 'Escalated', 'Escalated', 'sla_violation', '{"sla_hours_overdue": 48, "escalation_level": 2}', '192.168.1.1', 'System/1.0', now() - INTERVAL '2 hours'),

-- Case 5 logs (duplicate detection)
('750e8400-e29b-41d4-a716-446655440012', '650e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440001', 'case_created', NULL, 'Submitted', 'duplicate_detected', '{"origin_case_id": "650e8400-e29b-41d4-a716-446655440001", "duplicate_hash": "sha256_normalized_url_hash_001"}', '192.168.1.104', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', now() - INTERVAL '30 minutes');

-- Insert SLA timers
INSERT INTO sla_timers (case_id, timer_type, due_at, status) VALUES
('650e8400-e29b-41d4-a716-446655440001', 'review', now() + INTERVAL '48 hours', 'pending'),
('650e8400-e29b-41d4-a716-446655440002', 'review', now() + INTERVAL '24 hours', 'pending'),
('650e8400-e29b-41d4-a716-446655440003', 'review', now() - INTERVAL '2 hours', 'triggered'),
('650e8400-e29b-41d4-a716-446655440004', 'escalation', now() - INTERVAL '24 hours', 'triggered'),
('650e8400-e29b-41d4-a716-446655440005', 'review', now() + INTERVAL '48 hours', 'pending');

-- Insert sample notifications
INSERT INTO notifications (case_id, recipient_id, notification_type, title, message, severity, status, sent_at) VALUES
('650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'case_assigned', 'New Case Assigned', 'Case CASE-2025-0001 has been assigned to you for review', 'medium', 'sent', now() - INTERVAL '1 hour'),
('650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440004', 'case_assigned', 'High Priority Case Assigned', 'High priority case CASE-2025-0002 has been assigned to you', 'high', 'sent', now() - INTERVAL '2 hours'),
('650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'case_approved', 'Case Approved', 'Your case CASE-2025-0003 has been approved and action taken', 'low', 'sent', now() - INTERVAL '2 hours'),
('650e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440004', 'case_escalated', 'Case Escalated', 'Case CASE-2025-0004 has been escalated due to SLA violation', 'critical', 'sent', now() - INTERVAL '2 hours'),
('650e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440001', 'duplicate_detected', 'Duplicate Case Detected', 'Your submission matches existing case CASE-2025-0001', 'medium', 'sent', now() - INTERVAL '30 minutes');

-- Update audit log checksums
UPDATE audit_logs SET checksum = calculate_audit_checksum(log_id, case_id, actor_id, action, old_state, new_state, created_at);

-- Insert sample reports
INSERT INTO reports (case_id, generated_by, report_type, format, file_path, file_size_bytes, generated_at, expires_at) VALUES
('650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'audit', 'json', '/reports/audit_CASE-2025-0003.json', 2048, now() - INTERVAL '1 hour', now() + INTERVAL '30 days'),
('650e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440005', 'sla', 'csv', '/reports/sla_violations_2025-01-13.csv', 1024, now() - INTERVAL '30 minutes', now() + INTERVAL '7 days');

-- Verify data integrity
SELECT 'Data seeding completed successfully' as status;
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as case_count FROM cases;
SELECT COUNT(*) as submission_count FROM submissions;
SELECT COUNT(*) as audit_count FROM audit_logs;
SELECT COUNT(*) as notification_count FROM notifications;
