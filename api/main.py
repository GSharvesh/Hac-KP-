"""
Take It Down Backend - Main FastAPI Application
Victim-Led Content Removal System
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Take It Down Backend API",
    description="Victim-Led Content Removal System - Hackathon Project",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for testing
MOCK_CASES = {
    "650e8400-e29b-41d4-a716-446655440001": {
        "case_id": "650e8400-e29b-41d4-a716-446655440001",
        "case_ref": "CASE-2025-DEMO-001",
        "status": "submitted",
        "jurisdiction": "IN",
        "priority": "high",
        "submissions": [
            {"kind": "URL", "content": "https://demo-harmful.example.com/content123"},
            {"kind": "HASH", "content": "demo_hash_1234567890abcdef"}
        ],
        "notes": "Reported harmful content targeting minors",
        "created_at": "2025-01-13T10:00:00Z",
        "updated_at": "2025-01-13T10:00:00Z"
    }
}

MOCK_USERS = {
    "victim_jane_doe": {
        "username": "victim_jane_doe",
        "password": "secure_password_123",
        "role": "victim",
        "purpose": "takedown_submission"
    },
    "officer_alex_brown": {
        "username": "officer_alex_brown", 
        "password": "officer_password_123",
        "role": "officer",
        "purpose": "case_review"
    },
    "admin_mike_chen": {
        "username": "admin_mike_chen",
        "password": "admin_password_123", 
        "role": "admin",
        "purpose": "admin_action"
    }
}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "Take It Down Backend"
    }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        "total_cases": len(MOCK_CASES),
        "active_cases": len([c for c in MOCK_CASES.values() if c["status"] == "submitted"]),
        "resolved_cases": len([c for c in MOCK_CASES.values() if c["status"] == "approved"]),
        "uptime_seconds": 3600,  # Mock uptime
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication endpoints
@app.post("/v1/auth/login")
async def login(request: Request):
    """Login with purpose-binding JWT"""
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        purpose = body.get("purpose", "takedown_submission")
        
        if username not in MOCK_USERS:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = MOCK_USERS[username]
        if user["password"] != password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if user["purpose"] != purpose:
            raise HTTPException(status_code=403, detail="Invalid purpose for user role")
        
        # Mock JWT token
        token = f"mock_jwt_token_{username}_{purpose}_{datetime.utcnow().timestamp()}"
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "username": username,
                "role": user["role"],
                "purpose": purpose
            }
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# Case management endpoints
@app.post("/v1/cases/submit")
async def submit_case(request: Request):
    """Submit a new takedown case"""
    try:
        body = await request.json()
        
        # Generate mock case ID
        case_id = f"case_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{body.get('jurisdiction', 'XX')}"
        
        case_data = {
            "case_id": case_id,
            "case_ref": f"CASE-{datetime.utcnow().strftime('%Y-%m-%d')}-{len(MOCK_CASES)+1:03d}",
            "status": "submitted",
            "jurisdiction": body.get("jurisdiction"),
            "priority": body.get("priority", "medium"),
            "submissions": body.get("submissions", []),
            "notes": body.get("notes"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        MOCK_CASES[case_id] = case_data
        
        return {
            "case_id": case_id,
            "case_ref": case_data["case_ref"],
            "status": "submitted",
            "duplicate_detected": False,
            "message": "Case submitted successfully"
        }
    except Exception as e:
        logger.error(f"Case submission error: {e}")
        raise HTTPException(status_code=500, detail="Case submission failed")

@app.get("/v1/cases/{case_id}")
async def get_case(case_id: str):
    """Get case details"""
    if case_id not in MOCK_CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return MOCK_CASES[case_id]

@app.patch("/v1/cases/{case_id}")
async def update_case(case_id: str, request: Request):
    """Update case status"""
    try:
        if case_id not in MOCK_CASES:
            raise HTTPException(status_code=404, detail="Case not found")
        
        body = await request.json()
        action = body.get("action")
        reason_code = body.get("reason_code")
        notes = body.get("notes")
        
        case = MOCK_CASES[case_id]
        
        if action == "start_review":
            case["status"] = "under_review"
        elif action == "approve":
            case["status"] = "approved"
        elif action == "reject":
            case["status"] = "rejected"
        elif action == "close":
            case["status"] = "closed"
        
        case["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "case_id": case_id,
            "status": case["status"],
            "action": action,
            "reason_code": reason_code,
            "notes": notes,
            "updated_at": case["updated_at"]
        }
    except Exception as e:
        logger.error(f"Case update error: {e}")
        raise HTTPException(status_code=500, detail="Case update failed")

# Audit endpoints
@app.get("/v1/audit/{case_id}")
async def get_audit_trail(case_id: str):
    """Get case audit trail"""
    if case_id not in MOCK_CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Mock audit trail
    audit_logs = [
        {
            "log_id": f"audit_{case_id}_001",
            "case_id": case_id,
            "action": "case_created",
            "actor_name": "system",
            "old_state": None,
            "new_state": "submitted",
            "reason_code": "initial_submission",
            "created_at": MOCK_CASES[case_id]["created_at"]
        },
        {
            "log_id": f"audit_{case_id}_002", 
            "case_id": case_id,
            "action": "status_updated",
            "actor_name": "officer_alex_brown",
            "old_state": "submitted",
            "new_state": MOCK_CASES[case_id]["status"],
            "reason_code": "officer_review",
            "created_at": MOCK_CASES[case_id]["updated_at"]
        }
    ]
    
    return {
        "case_id": case_id,
        "logs": audit_logs,
        "total_logs": len(audit_logs)
    }

# Reporting endpoints
@app.get("/v1/reports/cases")
async def generate_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    format: str = "json"
):
    """Generate compliance report"""
    
    # Mock report data
    report_data = {
        "report_id": f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "format": format,
        "file_size_bytes": 1024,
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": {
            "total_cases": len(MOCK_CASES),
            "resolved_cases": len([c for c in MOCK_CASES.values() if c["status"] in ["approved", "rejected", "closed"]]),
            "sla_violations": 0,
            "compliance_percentage": 95.0,
            "average_resolution_hours": 24.5
        },
        "cases": list(MOCK_CASES.values())
    }
    
    return report_data

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Take It Down Backend API",
        "version": "1.0.0",
        "description": "Victim-Led Content Removal System",
        "docs_url": "/docs",
        "health_url": "/health",
        "metrics_url": "/metrics"
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
