#!/bin/bash

# Take It Down Backend - Demo Runner Script
# This script sets up and runs the complete demo

set -e

echo "🚀 Take It Down Backend - Hackathon Demo Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_info "Starting demo setup..."

# Create necessary directories
mkdir -p logs reports monitoring/grafana/dashboards monitoring/grafana/datasources nginx/ssl

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://takedown_user:takedown_pass@localhost:5432/takedown_backend

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=demo-jwt-secret-key-change-in-production
REDACTION_POLICY_VERSION=redaction_policy_v1.0

# SLA Configuration
REVIEW_SLA_HOURS=48
ESCALATION_GRACE_HOURS=2
MAX_ESCALATION_LEVELS=3

# Notification Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=demo@takedown-backend.gov
SMTP_PASSWORD=demo-password

# Demo Mode
DEMO_MODE=true
DEMO_SPEED_MULTIPLIER=10
EOF
    print_status "Created .env file"
fi

# Build and start services
print_info "Building Docker images..."
docker-compose build

print_info "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 10

# Check if services are running
print_info "Checking service health..."

# Check database
if docker-compose exec -T db pg_isready -U takedown_user -d takedown_backend > /dev/null 2>&1; then
    print_status "Database is ready"
else
    print_warning "Database is not ready yet, waiting..."
    sleep 10
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "Redis is ready"
else
    print_warning "Redis is not ready yet, waiting..."
    sleep 5
fi

# Check application
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Application is ready"
else
    print_warning "Application is not ready yet, waiting..."
    sleep 10
fi

# Run database migrations
print_info "Running database migrations..."
docker-compose exec -T app python -c "
import asyncio
import asyncpg
import os

async def run_migrations():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        with open('database/schema.sql', 'r') as f:
            await conn.execute(f.read())
        with open('database/seed_data.sql', 'r') as f:
            await conn.execute(f.read())
        print('Migrations completed successfully')
    finally:
        await conn.close()

asyncio.run(run_migrations())
"

print_status "Database migrations completed"

# Show service status
echo ""
print_info "Service Status:"
docker-compose ps

echo ""
print_info "Demo URLs:"
echo "  🌐 API Documentation: http://localhost:8000/docs"
echo "  🔍 Health Check: http://localhost:8000/health"
echo "  📊 Metrics: http://localhost:8000/metrics"
echo "  📈 Grafana (if enabled): http://localhost:3000"
echo "  🔧 Prometheus (if enabled): http://localhost:9090"

echo ""
print_info "Running demo scenarios..."

# Run the demo
docker-compose exec -T app python demo/demo_runner.py

echo ""
print_status "Demo completed successfully!"

echo ""
print_info "Next steps:"
echo "  1. Visit http://localhost:8000/docs to explore the API"
echo "  2. Use the provided Postman collection to test endpoints"
echo "  3. Check logs with: docker-compose logs -f app"
echo "  4. Stop services with: docker-compose down"

echo ""
print_info "API Examples:"
echo "  # Login as victim"
echo "  curl -X POST http://localhost:8000/v1/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\": \"victim_jane_doe\", \"password\": \"secure_password_123\", \"purpose\": \"takedown_submission\"}'"
echo ""
echo "  # Submit a case"
echo "  curl -X POST http://localhost:8000/v1/cases/submit \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\"
echo "    -d '{\"idempotency_key\": \"demo_001\", \"jurisdiction\": \"IN\", \"submissions\": [{\"kind\": \"URL\", \"content\": \"https://example.com/harmful\"}]}'"

echo ""
print_status "Take It Down Backend is ready for demonstration! 🎉"
