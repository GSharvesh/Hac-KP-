# Take It Down Backend - Project Scope & Safety Rules

## 🎯 Project Overview
**Victim-Led Content Removal System (BE02)** - A secure backend-only platform for processing content takedown requests with strict safety protocols and transparent audit trails.

## 🔒 Safety Rules & Input Constraints

### ✅ Allowed Inputs
| Input Type | Format | Example | Storage Method |
|------------|--------|---------|----------------|
| **URLs** | String (https://) | `https://example.com/harmful-content` | Normalized & hashed |
| **Content Hashes** | SHA256 string | `f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93f0a4e83f6e6e6b87a2a0f9` | Direct storage |
| **Metadata** | JSON object | `{"jurisdiction": "IN", "priority": "high"}` | Structured storage |
| **Case References** | String | `CASE-2025-0001` | Auto-generated |

### ❌ Forbidden Inputs
- Raw images, videos, or media files
- Base64-encoded content
- Screenshots or file uploads
- PII (phone numbers, emails) stored permanently
- Any content that could contain CSAM or illegal material

## 👥 User Roles & Permissions Matrix

| Permission | Victim | Officer | Admin |
|------------|--------|---------|-------|
| Submit Reports | ✅ | ❌ | ❌ |
| View Own Cases | ✅ | ✅ | ✅ |
| Review All Cases | ❌ | ✅ | ✅ |
| Approve/Reject | ❌ | ✅ | ✅ |
| Escalate Cases | ❌ | ✅ | ✅ |
| Export Reports | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ✅ |
| System Configuration | ❌ | ❌ | ✅ |

## 🏗️ Demo Scope (Backend Components)

### API Layer
- **POST** `/v1/submissions` - Submit takedown requests
- **GET** `/v1/cases/{id}` - Retrieve case details
- **PATCH** `/v1/cases/{id}/status` - Update case status
- **GET** `/v1/reports/audit` - Generate compliance reports
- **GET** `/v1/health` - System health check

### Database Schema
- `users` - User accounts and roles
- `cases` - Takedown requests and status
- `submissions` - Individual URLs/hashes per case
- `audit_logs` - Immutable action history
- `sla_timers` - Escalation tracking

### Background Workers
- SLA monitoring and auto-escalation
- Notification dispatch
- Report generation

## 🔐 Security Protocols

### Data Handling
- **Never store raw content** - Only URLs and hashes
- **Immutable audit logs** - Append-only with cryptographic integrity
- **Role-based access control** - JWT with purpose-binding
- **Input validation** - Strict URL/hash format checking

### Compliance Features
- **Policy versioning** - Track and enforce redaction policies
- **Lineage tracking** - Case ancestry for duplicate detection
- **Transparency logs** - Tamper-proof JSONL manifest
- **SLA enforcement** - Automated escalation with reason codes

## 📊 Sample Test Dataset

### Fake URLs (Safe for Testing)
```
https://fake-report.com/content123
https://demo-case.org/abc456
https://test-takedown.net/sample789
```

### Fake Hashes (SHA256)
```
1234abcd5678efgh91011ijklmnopqrstuvwx1234abcd5678efgh91011ijklmnop
9876zyxw5432vuts1098rqpo7654nmlkjihgfedcba9876zyxw5432vuts1098rqpo
```

### Sample Cases
| Case ID | URL | Hash | Status | Submitter | Created |
|---------|-----|------|--------|-----------|---------|
| CASE-001 | https://fake-report.com/c123 | NULL | Submitted | victim_001 | 2025-01-13 10:00 |
| CASE-002 | NULL | 1234ab... | In Review | victim_002 | 2025-01-13 10:05 |
| CASE-003 | https://demo-case.org/abc456 | NULL | Approved | officer_001 | 2025-01-13 10:10 |

## 🚨 Emergency Protocols
- **Immediate shutdown** if raw content detected
- **Audit log preservation** for forensic analysis
- **Role escalation** for security incidents
- **Data retention** policies (90-day minimum)

## 📋 Policy Versioning
- **Current Version**: `redaction_policy_v1.0`
- **API Compatibility**: Reject submissions with outdated policies
- **Migration Path**: Automatic policy updates with grace periods

---
*This scope document ensures safe, compliant, and transparent operation of the Take It Down backend system.*
