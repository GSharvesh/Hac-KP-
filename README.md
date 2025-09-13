# Take It Down Backend - Victim-Led Content Removal System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com/)

A secure, scalable backend system for processing victim-led content takedown requests with comprehensive audit trails, SLA management, and compliance reporting.

## 🎯 Hackathon Project Overview

**Project**: Take It Down (BE02) - Victim-Led Content Removal Backend  
**Focus**: Backend-only implementation with safety-first design  
**Unique Features**: Purpose-binding JWT, case lineage tracking, tamper-proof audit logs

## 🚀 Key Features

### 🔒 Safety & Security
- **Never stores raw content** - Only URLs and SHA256 hashes
- **Purpose-binding JWT** - Tokens restricted to specific actions
- **Role-based access control** - Victim, Officer, Admin permissions
- **Input validation** - Strict URL/hash format checking

### 🔄 Workflow Management
- **State machine** - Clear case lifecycle with reason codes
- **SLA enforcement** - Automated escalation with configurable deadlines
- **Deduplication** - Automatic detection of duplicate submissions
- **Lineage tracking** - Case ancestry for forensic analysis

### 📊 Compliance & Reporting
- **Tamper-proof audit logs** - Cryptographic integrity verification
- **Transparency logs** - Append-only JSONL manifest
- **Compliance metrics** - SLA performance and violation tracking
- **Export capabilities** - JSON, CSV, PDF report generation

### 🔔 Notifications
- **Multi-channel alerts** - Email, SMS, Slack, Webhook
- **Severity-based routing** - Different channels for different priorities
- **SLA warnings** - Proactive alerts before deadline
- **Retry mechanism** - Failed notification recovery

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Authentication │    │  Workflow Engine│
│   (FastAPI)     │◄──►│  (JWT + RBAC)   │◄──►│  (State Machine)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │  Notifications  │    │  Compliance     │
│   (PostgreSQL)  │    │  (Multi-channel)│    │  (Audit + Reports)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Redis (optional, for background workers)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/takedown-backend.git
   cd takedown-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup database**
   ```bash
   # Create database
   createdb takedown_backend
   
   # Run migrations
   psql takedown_backend < database/schema.sql
   psql takedown_backend < database/seed_data.sql
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Demo Mode

Run the interactive demo to see the system in action:

```bash
python demo/demo_runner.py
```

## 📚 API Documentation

### Authentication
```bash
# Login with purpose-binding
POST /v1/auth/login
{
  "username": "victim_jane_doe",
  "password": "secure_password_123",
  "purpose": "takedown_submission"
}
```

### Case Management
```bash
# Submit takedown request
POST /v1/cases/submit
{
  "idempotency_key": "sub_2025_001",
  "jurisdiction": "IN",
  "priority": "high",
  "submissions": [
    {"kind": "URL", "content": "https://example.com/harmful-content"},
    {"kind": "HASH", "content": "sha256_hash_here"}
  ]
}

# Get case details
GET /v1/cases/{case_id}

# Update case status
PATCH /v1/cases/{case_id}
{
  "action": "approve",
  "reason_code": "content_verified_harmful",
  "notes": "Content verified as harmful"
}
```

### Reporting
```bash
# Generate compliance report
GET /v1/reports/cases?from_date=2025-01-01&format=json

# Get case audit trail
GET /v1/audit/{case_id}
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/takedown_backend

# Security
JWT_SECRET=your-super-secret-jwt-key
REDACTION_POLICY_VERSION=redaction_policy_v1.0

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@takedown-backend.gov
SMTP_PASSWORD=your-email-password

# SLA Configuration
REVIEW_SLA_HOURS=48
ESCALATION_GRACE_HOURS=2
MAX_ESCALATION_LEVELS=3
```

### Database Schema
The system uses PostgreSQL with the following key tables:
- `users` - User accounts and roles
- `cases` - Takedown requests and status
- `submissions` - Individual URLs/hashes per case
- `audit_logs` - Immutable action history
- `sla_timers` - Escalation tracking

## 🛡️ Security Features

### Purpose-Binding JWT
Each JWT token includes a `purpose` claim that restricts its usage:
- `takedown_submission` - Only for victim submissions
- `case_review` - Only for officer case management
- `admin_action` - Only for administrative functions
- `report_generation` - Only for report access

### Input Validation
- URLs must match `https://` pattern
- Hashes must be valid SHA256 format
- All inputs are sanitized and validated
- No raw content is ever stored

### Audit Logging
- Every action creates an immutable audit log
- Cryptographic checksums prevent tampering
- Complete case timeline tracking
- Transparency log for external verification

## 📊 Monitoring & Metrics

### Health Endpoints
```bash
# System health
GET /health

# Performance metrics
GET /metrics
```

### Compliance Metrics
- SLA compliance percentage
- Average resolution time
- Escalation rates
- False positive rates
- Jurisdiction breakdown

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t takedown-backend .

# Run with docker-compose
docker-compose up -d
```

### Production Considerations
- Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Configure Redis for background workers
- Set up monitoring (Prometheus, Grafana)
- Enable HTTPS with valid certificates
- Configure log aggregation (ELK stack)

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/
```

### Demo Scenarios
The demo includes realistic scenarios:
1. **Successful High-Priority Case** - Quick approval workflow
2. **SLA Violation and Escalation** - Automated escalation handling
3. **Duplicate Detection** - Smart deduplication system
4. **False Positive Rejection** - Safe content handling

## 📈 Performance

### Benchmarks
- **Throughput**: 1000+ cases/hour
- **Response Time**: <200ms average
- **SLA Compliance**: 95%+ on-time resolution
- **Uptime**: 99.9% availability target

### Scaling
- Horizontal scaling with load balancers
- Database read replicas for reporting
- Background worker scaling
- Caching for frequently accessed data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/takedown-backend/issues)
- **Email**: support@takedown-backend.gov

## 🏆 Hackathon Features

### Unique Value Propositions
1. **Purpose-Binding JWT** - Novel security control preventing token reuse
2. **Case Lineage Tracking** - Forensic analysis of case relationships
3. **Tamper-Proof Audit Logs** - Cryptographic integrity verification
4. **Severity-Based Notifications** - Smart routing based on urgency
5. **Policy Versioning** - Forward-thinking compliance management

### Demo Highlights
- **Case Lifecycle Replay** - Realistic scenario demonstration
- **Real-time Metrics** - Live system health monitoring
- **Interactive API** - Swagger UI for testing
- **Compliance Reports** - Judge-ready documentation

---

**Built for Hac'KP 2025 - Victim-Led Content Removal Backend Challenge**

*This system ensures safe, compliant, and transparent processing of content takedown requests while maintaining the highest standards of security and accountability.*
