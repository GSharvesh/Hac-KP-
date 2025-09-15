# Take It Down Backend - UML Diagrams

This document contains comprehensive UML diagrams for the Take It Down Backend - Victim-Led Content Removal System.

## 1. System Architecture Component Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Client]
        API_CLIENT[API Client]
        MOBILE[Mobile App]
    end
    
    subgraph "API Gateway Layer"
        NGINX[Nginx Reverse Proxy]
        FASTAPI[FastAPI Application]
        CORS[CORS Middleware]
    end
    
    subgraph "Authentication & Security"
        AUTH[Authentication Service]
        JWT[JWT Token Service]
        RBAC[Role-Based Access Control]
        MIDDLEWARE[Security Middleware]
    end
    
    subgraph "Business Logic Layer"
        WORKFLOW[Workflow Engine]
        STATE_MACHINE[State Machine]
        SLA_PROCESSOR[SLA Processor]
        DEDUP[Deduplication Service]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL Database)]
        REDIS[(Redis Cache)]
        AUDIT_DB[(Audit Logs)]
    end
    
    subgraph "External Services"
        NOTIFICATIONS[Notification Service]
        EMAIL[Email Service]
        SMS[SMS Service]
        WEBHOOK[Webhook Service]
    end
    
    subgraph "Background Processing"
        WORKER[SLA Worker]
        CELERY[Celery Tasks]
        SCHEDULER[Task Scheduler]
    end
    
    subgraph "Reporting & Compliance"
        COMPLIANCE[Compliance Engine]
        REPORTS[Report Generator]
        TRANSPARENCY[Transparency Logs]
        METRICS[Metrics Collector]
    end
    
    subgraph "Monitoring"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        HEALTH[Health Checks]
    end
    
    %% Client connections
    WEB --> NGINX
    API_CLIENT --> NGINX
    MOBILE --> NGINX
    
    %% API Gateway flow
    NGINX --> FASTAPI
    FASTAPI --> CORS
    CORS --> MIDDLEWARE
    
    %% Authentication flow
    MIDDLEWARE --> AUTH
    AUTH --> JWT
    AUTH --> RBAC
    
    %% Business logic flow
    FASTAPI --> WORKFLOW
    WORKFLOW --> STATE_MACHINE
    WORKFLOW --> SLA_PROCESSOR
    WORKFLOW --> DEDUP
    
    %% Data layer connections
    WORKFLOW --> POSTGRES
    WORKFLOW --> REDIS
    WORKFLOW --> AUDIT_DB
    
    %% External service connections
    WORKFLOW --> NOTIFICATIONS
    NOTIFICATIONS --> EMAIL
    NOTIFICATIONS --> SMS
    NOTIFICATIONS --> WEBHOOK
    
    %% Background processing
    WORKER --> POSTGRES
    WORKER --> REDIS
    CELERY --> WORKER
    SCHEDULER --> CELERY
    
    %% Reporting connections
    FASTAPI --> COMPLIANCE
    COMPLIANCE --> REPORTS
    COMPLIANCE --> TRANSPARENCY
    COMPLIANCE --> METRICS
    
    %% Monitoring connections
    FASTAPI --> HEALTH
    METRICS --> PROMETHEUS
    PROMETHEUS --> GRAFANA
```

## 2. Class Diagram - Core Domain Models

```mermaid
classDiagram
    class User {
        +UUID user_id
        +String username
        +String email
        +UserRole role
        +String jurisdiction
        +Boolean is_active
        +DateTime last_login_at
        +DateTime created_at
        +DateTime updated_at
        +authenticate(password: String) Boolean
        +hasPermission(action: String) Boolean
    }
    
    class Case {
        +UUID case_id
        +String case_ref
        +UUID submitter_id
        +UUID assigned_officer_id
        +CaseStatus status
        +String jurisdiction
        +CasePriority priority
        +UUID origin_case_id
        +Integer lineage_depth
        +DateTime sla_due_at
        +Boolean sla_violated
        +Integer escalation_level
        +DateTime created_at
        +DateTime updated_at
        +DateTime resolved_at
        +String policy_version
        +String notes
        +submit() Boolean
        +assignOfficer(officerId: UUID) Boolean
        +updateStatus(status: CaseStatus) Boolean
        +escalate() Boolean
    }
    
    class Submission {
        +UUID submission_id
        +UUID case_id
        +SubmissionKind kind
        +String content
        +String normalized_content
        +String dedup_hash
        +DateTime created_at
        +validate() Boolean
        +normalize() String
        +generateHash() String
    }
    
    class AuditLog {
        +UUID log_id
        +UUID case_id
        +UUID actor_id
        +String action
        +String old_state
        +String new_state
        +String reason_code
        +JSONB meta
        +String ip_address
        +String user_agent
        +DateTime created_at
        +String checksum
        +calculateChecksum() String
        +verifyIntegrity() Boolean
    }
    
    class WorkflowEngine {
        -Map transitions
        -Map sla_config
        +canTransition(context: CaseContext, action: String, userRole: String) Tuple
        +executeTransition(context: CaseContext, action: String, userId: String, userRole: String) Tuple
        +getAvailableActions(context: CaseContext, userRole: String) List
        +getSlaStatus(context: CaseContext) String
        +shouldEscalate(context: CaseContext) Boolean
    }
    
    class CaseContext {
        +String case_id
        +CaseStatus current_status
        +CasePriority priority
        +String jurisdiction
        +String submitter_id
        +String assigned_officer_id
        +Integer escalation_level
        +DateTime sla_due_at
        +DateTime created_at
        +DateTime updated_at
    }
    
    class StateTransition {
        +CaseStatus from_status
        +CaseStatus to_status
        +ReasonCode reason_code
        +String required_role
        +Integer sla_hours
        +Boolean auto_escalation
        +String description
    }
    
    class AuthenticationService {
        -SecurityConfig config
        -PasswordValidator validator
        -TokenService token_service
        +authenticate(username: String, password: String, purpose: String) TokenClaims
        +validateToken(token: String) TokenClaims
        +refreshToken(token: String) String
        +revokeToken(token: String) Boolean
    }
    
    class NotificationService {
        -Map templates
        -List channels
        +sendNotification(caseId: String, type: String, recipientId: String, severity: String) Boolean
        +notifyCaseEscalation(caseId: String, level: Integer, officerId: String) Boolean
        +notifySlaWarning(caseId: String, hoursRemaining: Integer, officerId: String) Boolean
    }
    
    class ComplianceEngine {
        -TransparencyLogger logger
        -ReportGenerator generator
        +generateMetrics(fromDate: DateTime, toDate: DateTime) ComplianceMetrics
        +generateReport(type: ReportType, format: ReportFormat) Report
        +logTransparencyEvent(event: TransparencyEvent) Boolean
        +verifyAuditIntegrity(caseId: String) Boolean
    }
    
    %% Relationships
    User ||--o{ Case : submits
    User ||--o{ Case : assigned_to
    User ||--o{ AuditLog : performs
    Case ||--o{ Submission : contains
    Case ||--o{ AuditLog : generates
    Case ||--o{ Case : lineage
    WorkflowEngine --> CaseContext : manages
    WorkflowEngine --> StateTransition : defines
    AuthenticationService --> User : authenticates
    NotificationService --> Case : notifies
    ComplianceEngine --> Case : reports
```

## 3. Sequence Diagram - Case Submission Workflow

```mermaid
sequenceDiagram
    participant V as Victim
    participant API as FastAPI
    participant AUTH as AuthService
    participant WORKFLOW as WorkflowEngine
    participant DB as Database
    participant AUDIT as AuditLogger
    participant NOTIFY as NotificationService
    participant OFFICER as Officer
    
    V->>API: POST /v1/auth/login
    Note over V,API: {username, password, purpose}
    
    API->>AUTH: authenticate(username, password, purpose)
    AUTH-->>API: TokenClaims + JWT
    API-->>V: {access_token, user_info}
    
    V->>API: POST /v1/cases/submit
    Note over V,API: {jurisdiction, priority, submissions[]}
    Note over V,API: Authorization: Bearer JWT
    
    API->>AUTH: validateToken(jwt)
    AUTH-->>API: TokenClaims (validated)
    
    API->>WORKFLOW: createCase(submission_data)
    WORKFLOW->>DB: checkDuplicate(submissions)
    DB-->>WORKFLOW: duplicate_status
    
    alt No Duplicate Found
        WORKFLOW->>DB: insertCase(case_data)
        DB-->>WORKFLOW: case_id
        WORKFLOW->>AUDIT: logEvent(case_created)
        AUDIT-->>WORKFLOW: audit_log_id
        
        WORKFLOW->>NOTIFY: notifyCaseSubmitted(case_id)
        NOTIFY-->>WORKFLOW: notification_sent
        
        WORKFLOW->>DB: assignOfficer(case_id)
        DB-->>WORKFLOW: officer_assigned
        
        WORKFLOW->>NOTIFY: notifyOfficerAssignment(case_id, officer_id)
        NOTIFY-->>WORKFLOW: notification_sent
        
        WORKFLOW-->>API: {case_id, status: "submitted"}
        API-->>V: {case_id, case_ref, status}
    else Duplicate Found
        WORKFLOW->>AUDIT: logEvent(duplicate_detected)
        AUDIT-->>WORKFLOW: audit_log_id
        WORKFLOW-->>API: {duplicate_case_id, status: "duplicate"}
        API-->>V: {duplicate_case_id, message: "Duplicate detected"}
    end
    
    Note over OFFICER: Officer receives notification
    OFFICER->>API: PATCH /v1/cases/{case_id}
    Note over OFFICER,API: {action: "start_review"}
    
    API->>WORKFLOW: updateCaseStatus(case_id, "start_review")
    WORKFLOW->>DB: updateCaseStatus(case_id, "In Review")
    WORKFLOW->>AUDIT: logEvent(status_changed)
    WORKFLOW-->>API: {status: "In Review", sla_due_at}
    API-->>OFFICER: {case_id, status, sla_due_at}
```

## 4. State Machine Diagram - Case Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Submitted : Case Created
    
    Submitted --> InReview : Officer Assignment<br/>reason: officer_assignment
    Submitted --> Rejected : False Report<br/>reason: false_report
    
    InReview --> Approved : Content Verified Harmful<br/>reason: content_verified_harmful
    InReview --> Rejected : Content Verified Safe<br/>reason: content_verified_safe
    InReview --> Escalated : SLA Violation<br/>reason: sla_violation
    InReview --> Escalated : Manual Escalation<br/>reason: manual_escalation
    
    Escalated --> InReview : Reassignment<br/>reason: manual_escalation
    Escalated --> Closed : Admin Override<br/>reason: admin_override
    
    Approved --> Closed : Resolution Complete<br/>reason: case_closed
    Rejected --> Closed : Case Closed<br/>reason: case_closed
    
    Closed --> [*]
    
    note right of Submitted
        Initial state
        - SLA timer starts
        - Officer assignment
        - Notification sent
    end note
    
    note right of InReview
        Active review state
        - SLA monitoring active
        - Officer can approve/reject
        - Auto-escalation possible
    end note
    
    note right of Escalated
        SLA violation state
        - Higher priority handling
        - Admin intervention
        - Shorter SLA for reassignment
    end note
    
    note right of Approved
        Content verified harmful
        - Takedown action taken
        - Resolution tracking
        - Final closure pending
    end note
    
    note right of Rejected
        Content verified safe
        - No action required
        - False positive tracking
        - Case closure
    end note
    
    note right of Closed
        Final state
        - Audit trail complete
        - Compliance metrics updated
        - No further transitions
    end note
```

## 5. Database Entity Relationship Diagram

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
    USERS ||--o{ AUDIT_LOGS : "performs"
    USERS ||--o{ REPORTS : "generates"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ SYSTEM_CONFIG : "updates"
    
    CASES ||--o{ SUBMISSIONS : "contains"
    CASES ||--o{ AUDIT_LOGS : "generates"
    CASES ||--o{ SLA_TIMERS : "has"
    CASES ||--o{ REPORTS : "reports_on"
    CASES ||--o{ NOTIFICATIONS : "triggers"
    CASES ||--o{ CASES : "lineage"
```

## 6. Use Case Diagram

```mermaid
graph TB
    subgraph "Take It Down Backend System"
        subgraph "Victim Use Cases"
            UC1[Submit Takedown Request]
            UC2[View Own Cases]
            UC3[Track Case Status]
        end
        
        subgraph "Officer Use Cases"
            UC4[Review Cases]
            UC5[Approve/Reject Cases]
            UC6[Assign Cases]
            UC7[Escalate Cases]
            UC8[Generate Reports]
        end
        
        subgraph "Admin Use Cases"
            UC9[Manage Users]
            UC10[System Configuration]
            UC11[View All Cases]
            UC12[Override Decisions]
            UC13[System Monitoring]
        end
        
        subgraph "System Use Cases"
            UC14[Duplicate Detection]
            UC15[SLA Monitoring]
            UC16[Auto Escalation]
            UC17[Audit Logging]
            UC18[Notification Sending]
            UC19[Compliance Reporting]
        end
    end
    
    subgraph "Actors"
        VICTIM[Victim]
        OFFICER[Content Officer]
        ADMIN[System Admin]
        SYSTEM[System]
    end
    
    %% Victim interactions
    VICTIM --> UC1
    VICTIM --> UC2
    VICTIM --> UC3
    
    %% Officer interactions
    OFFICER --> UC4
    OFFICER --> UC5
    OFFICER --> UC6
    OFFICER --> UC7
    OFFICER --> UC8
    
    %% Admin interactions
    ADMIN --> UC9
    ADMIN --> UC10
    ADMIN --> UC11
    ADMIN --> UC12
    ADMIN --> UC13
    
    %% System interactions
    SYSTEM --> UC14
    SYSTEM --> UC15
    SYSTEM --> UC16
    SYSTEM --> UC17
    SYSTEM --> UC18
    SYSTEM --> UC19
    
    %% Cross-actor interactions
    UC1 -.-> UC14 : triggers
    UC4 -.-> UC15 : monitored by
    UC5 -.-> UC17 : logged by
    UC7 -.-> UC18 : triggers
```

## 7. Activity Diagram - SLA Violation Handling

```mermaid
flowchart TD
    START([SLA Worker Starts]) --> CHECK{Check Cases<br/>In Review}
    
    CHECK -->|Cases Found| LOOP[For Each Case]
    CHECK -->|No Cases| WAIT[Wait 5 Minutes]
    WAIT --> CHECK
    
    LOOP --> SLA_CHECK{SLA Due Date<br/>Exceeded?}
    
    SLA_CHECK -->|No| NEXT[Next Case]
    SLA_CHECK -->|Yes| ESCALATION_LEVEL{Current<br/>Escalation Level}
    
    ESCALATION_LEVEL -->|Level 0| LEVEL1[Escalate to Level 1<br/>Notify Officer]
    ESCALATION_LEVEL -->|Level 1| LEVEL2[Escalate to Level 2<br/>Notify Supervisor]
    ESCALATION_LEVEL -->|Level 2| LEVEL3[Escalate to Level 3<br/>Notify Admin]
    ESCALATION_LEVEL -->|Level 3| MAX_ESCALATION[Max Escalation<br/>Reached - Alert Admin]
    
    LEVEL1 --> AUDIT_LOG1[Log Escalation Event]
    LEVEL2 --> AUDIT_LOG2[Log Escalation Event]
    LEVEL3 --> AUDIT_LOG3[Log Escalation Event]
    MAX_ESCALATION --> AUDIT_LOG_MAX[Log Critical Event]
    
    AUDIT_LOG1 --> NOTIFY1[Send Notification]
    AUDIT_LOG2 --> NOTIFY2[Send Notification]
    AUDIT_LOG3 --> NOTIFY3[Send Notification]
    AUDIT_LOG_MAX --> NOTIFY_MAX[Send Critical Alert]
    
    NOTIFY1 --> UPDATE_STATUS1[Update Case Status<br/>to Escalated]
    NOTIFY2 --> UPDATE_STATUS2[Update Case Status<br/>to Escalated]
    NOTIFY3 --> UPDATE_STATUS3[Update Case Status<br/>to Escalated]
    NOTIFY_MAX --> UPDATE_STATUS_MAX[Update Case Status<br/>to Critical]
    
    UPDATE_STATUS1 --> NEXT
    UPDATE_STATUS2 --> NEXT
    UPDATE_STATUS3 --> NEXT
    UPDATE_STATUS_MAX --> NEXT
    
    NEXT --> MORE_CASES{More Cases<br/>to Process?}
    MORE_CASES -->|Yes| LOOP
    MORE_CASES -->|No| WAIT
    
    %% Error handling
    LEVEL1 -.->|Error| ERROR_LOG[Log Error]
    LEVEL2 -.->|Error| ERROR_LOG
    LEVEL3 -.->|Error| ERROR_LOG
    MAX_ESCALATION -.->|Error| ERROR_LOG
    ERROR_LOG --> NEXT
```

## 8. Deployment Diagram

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Load Balancer Tier"
            LB[Nginx Load Balancer<br/>SSL Termination]
        end
        
        subgraph "Application Tier"
            APP1[FastAPI App Instance 1<br/>Port 8000]
            APP2[FastAPI App Instance 2<br/>Port 8000]
            APP3[FastAPI App Instance 3<br/>Port 8000]
        end
        
        subgraph "Background Processing"
            WORKER1[SLA Worker 1]
            WORKER2[SLA Worker 2]
            CELERY[Celery Task Queue]
        end
        
        subgraph "Database Tier"
            DB_MASTER[(PostgreSQL Master<br/>Port 5432)]
            DB_REPLICA1[(PostgreSQL Replica 1<br/>Read Only)]
            DB_REPLICA2[(PostgreSQL Replica 2<br/>Read Only)]
        end
        
        subgraph "Cache Tier"
            REDIS_MASTER[(Redis Master<br/>Port 6379)]
            REDIS_REPLICA[(Redis Replica<br/>Port 6379)]
        end
        
        subgraph "Monitoring Tier"
            PROMETHEUS[Prometheus<br/>Port 9090]
            GRAFANA[Grafana<br/>Port 3000]
            ALERTMANAGER[AlertManager<br/>Port 9093]
        end
        
        subgraph "Storage Tier"
            FILES[File Storage<br/>Reports & Logs]
            BACKUP[Backup Storage<br/>Daily Snapshots]
        end
    end
    
    subgraph "External Services"
        SMTP[SMTP Server<br/>Email Notifications]
        SMS_API[SMS Gateway<br/>Text Notifications]
        WEBHOOK_API[Webhook Endpoints<br/>External Integrations]
    end
    
    %% Load balancer connections
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    %% Application connections
    APP1 --> DB_MASTER
    APP2 --> DB_MASTER
    APP3 --> DB_MASTER
    
    APP1 --> DB_REPLICA1
    APP2 --> DB_REPLICA2
    APP3 --> DB_REPLICA1
    
    APP1 --> REDIS_MASTER
    APP2 --> REDIS_MASTER
    APP3 --> REDIS_MASTER
    
    %% Background processing connections
    WORKER1 --> DB_MASTER
    WORKER2 --> DB_MASTER
    WORKER1 --> REDIS_MASTER
    WORKER2 --> REDIS_MASTER
    CELERY --> WORKER1
    CELERY --> WORKER2
    
    %% Database replication
    DB_MASTER -.->|Replication| DB_REPLICA1
    DB_MASTER -.->|Replication| DB_REPLICA2
    REDIS_MASTER -.->|Replication| REDIS_REPLICA
    
    %% Monitoring connections
    APP1 --> PROMETHEUS
    APP2 --> PROMETHEUS
    APP3 --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERTMANAGER
    
    %% Storage connections
    APP1 --> FILES
    APP2 --> FILES
    APP3 --> FILES
    DB_MASTER --> BACKUP
    
    %% External service connections
    APP1 --> SMTP
    APP2 --> SMS_API
    APP3 --> WEBHOOK_API
```

## Summary

These UML diagrams provide a comprehensive view of the Take It Down Backend system:

1. **Component Diagram**: Shows the overall system architecture and how components interact
2. **Class Diagram**: Details the core domain models and their relationships
3. **Sequence Diagram**: Illustrates the case submission workflow
4. **State Machine**: Shows the complete case lifecycle with all possible transitions
5. **ER Diagram**: Database schema with all tables and relationships
6. **Use Case Diagram**: User interactions and system capabilities
7. **Activity Diagram**: SLA violation handling process
8. **Deployment Diagram**: Production environment setup

The system follows a microservices architecture with clear separation of concerns, comprehensive audit logging, and robust SLA management for victim-led content removal requests.
