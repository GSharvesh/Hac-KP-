# Take It Down Backend - Application Instructions

## Overview

**Take It Down Backend** is a secure, scalable backend system designed for processing victim-led content takedown requests. It provides comprehensive audit trails, SLA management, and compliance reporting to ensure safe and transparent content removal workflows.

## Key Features and Functionalities

### Safety & Security
- Does not store raw content; only URLs and SHA256 hashes are stored.
- Purpose-binding JWT tokens restrict token usage to specific actions.
- Role-based access control with Victim, Officer, and Admin permissions.
- Strict input validation for URLs and hashes.
- Immutable, tamper-proof audit logs with cryptographic integrity.

### Workflow Management
- State machine to manage clear case lifecycle with reason codes.
- SLA enforcement with automated escalation and configurable deadlines.
- Automatic detection and handling of duplicate submissions.
- Case lineage tracking for forensic analysis.

### Compliance & Reporting
- Transparency logs with append-only JSONL manifests.
- Compliance metrics including SLA performance and violation tracking.
- Export capabilities for JSON, CSV, and PDF reports.

### Notifications
- Multi-channel alerts via Email, SMS, Slack, and Webhook.
- Severity-based routing for different priority levels.
- SLA warnings and retry mechanisms for failed notifications.

## Architecture

The system consists of the following components:
- API Gateway (FastAPI)
- Authentication (JWT + RBAC)
- Workflow Engine (State Machine)
- PostgreSQL Database
- Notifications (Multi-channel)
- Compliance (Audit logs and reports)

## How to Run the Application

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 13 or higher
- Redis (optional, for background workers)
- Docker and Docker Compose (optional, for containerized deployment)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/takedown-backend.git
   cd takedown-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup the database**
   - Create the PostgreSQL database:
     ```bash
     createdb takedown_backend
     ```
   - Run the schema and seed data SQL scripts:
     ```bash
     psql takedown_backend < database/schema.sql
     psql takedown_backend < database/seed_data.sql
     ```

4. **Configure environment variables**
   - Copy the example environment file and edit as needed:
     ```bash
     cp .env.example .env
     ```
   - Update `.env` with your database URL, JWT secret, SMTP settings, and other configurations.

5. **Run the application**
   ```bash
   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Run the demo (optional)**
   To see the system in action with realistic scenarios:
   ```bash
   python demo/demo_runner.py
   ```

### Running with Docker (Optional)

1. **Build and start services**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. **Check service health**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Metrics: http://localhost:8000/metrics

3. **Stop services**
   ```bash
   docker-compose down
   ```

## API Documentation

The API provides endpoints for authentication, case management, reporting, and audit logs. The interactive Swagger UI is available at `/docs` when the application is running.

## Testing

- Unit, integration, and API tests can be run using:
  ```bash
  pytest tests/unit/
  pytest tests/integration/
  pytest tests/api/
  ```

## Additional Notes

- The system supports multi-channel notifications and SLA enforcement.
- It includes a demo runner to simulate case lifecycles and system behavior.
- Monitoring and visualization can be enabled with Prometheus and Grafana.

---

This document provides a comprehensive guide to understanding and running the Take It Down backend application.
