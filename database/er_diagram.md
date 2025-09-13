# Database Entity Relationship Diagram

## Take It Down Backend - Database Schema

```mermaid
erDiagram
    USERS {
        uuid user_id PK
        varchar username UK
        varchar email UK
        varchar role
        varchar jurisdiction
        boolean is_active
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }
    
    CASES {
        uuid case_id PK
        varchar case_ref UK
        uuid submitter_id FK
        uuid assigned_officer_id FK
        varchar status
        varchar jurisdiction
        varchar priority
        uuid origin_case_id FK
        integer lineage_depth
        timestamp sla_due_at
        boolean sla_violated
        integer escalation_level
        timestamp created_at
        timestamp updated_at
        timestamp resolved_at
        varchar policy_version
        text notes
    }
    
    SUBMISSIONS {
        uuid submission_id PK
        uuid case_id FK
        varchar kind
        text content
        text normalized_content
        varchar dedup_hash
        timestamp created_at
    }
    
    AUDIT_LOGS {
        uuid log_id PK
        uuid case_id FK
        uuid actor_id FK
        varchar action
        text old_state
        text new_state
        varchar reason_code
        jsonb meta
        inet ip_address
        text user_agent
        timestamp created_at
        varchar checksum
    }
    
    SLA_TIMERS {
        uuid timer_id PK
        uuid case_id FK
        varchar timer_type
        timestamp due_at
        timestamp triggered_at
        varchar status
        timestamp created_at
    }
    
    REPORTS {
        uuid report_id PK
        uuid case_id FK
        uuid generated_by FK
        varchar report_type
        varchar format
        text file_path
        bigint file_size_bytes
        timestamp generated_at
        timestamp expires_at
    }
    
    NOTIFICATIONS {
        uuid notification_id PK
        uuid case_id FK
        uuid recipient_id FK
        varchar notification_type
        varchar title
        text message
        varchar severity
        varchar status
        timestamp sent_at
        timestamp created_at
    }
    
    SYSTEM_CONFIG {
        varchar config_key PK
        text config_value
        text description
        uuid updated_by FK
        timestamp updated_at
    }

    %% Relationships
    USERS ||--o{ CASES : "submits"
    USERS ||--o{ CASES : "assigned_to"
    CASES ||--o{ SUBMISSIONS : "contains"
    CASES ||--o{ AUDIT_LOGS : "has_logs"
    USERS ||--o{ AUDIT_LOGS : "performs_actions"
    CASES ||--o{ SLA_TIMERS : "has_timers"
    CASES ||--o{ REPORTS : "generates"
    USERS ||--o{ REPORTS : "creates"
    CASES ||--o{ NOTIFICATIONS : "triggers"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ SYSTEM_CONFIG : "updates"
    CASES ||--o{ CASES : "originates_from"
```

## Key Features

### 🔗 Lineage Tracking
- **origin_case_id**: Links duplicate cases to their original
- **lineage_depth**: Tracks how many generations deep a case is
- Enables forensic analysis of case relationships

### 🔍 Deduplication
- **dedup_hash**: SHA256 hash of normalized content
- **normalized_content**: Cleaned URL/hash for comparison
- Prevents duplicate submissions across cases

### 📊 Audit Trail
- **reason_code**: Structured reason for each action
- **checksum**: Cryptographic integrity verification
- **meta**: Rich JSON metadata for context

### ⏰ SLA Management
- **sla_timers**: Background job tracking
- **escalation_level**: Multi-level escalation support
- **sla_violated**: Compliance flagging

### 🔔 Notifications
- **severity**: Priority levels (low, medium, high, critical)
- **status**: Delivery tracking
- **notification_type**: Categorized alerts

## Indexes for Performance

```sql
-- Critical indexes for fast lookups
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_sla_due ON cases(sla_due_at) WHERE status = 'In Review';
CREATE INDEX idx_submissions_dedup ON submissions(dedup_hash);
CREATE INDEX idx_audit_case ON audit_logs(case_id);
CREATE INDEX idx_sla_timers_due ON sla_timers(due_at) WHERE status = 'pending';
```

## Views for Common Queries

- **case_summary**: Aggregated case information with SLA status
- **sla_metrics**: Compliance statistics by jurisdiction and date
