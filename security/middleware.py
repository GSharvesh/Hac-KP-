"""
Take It Down Backend - Security Middleware
FastAPI middleware for authentication and authorization
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from typing import Optional, Dict, Any
import json

from auth import AuthenticationService, SecurityConfig, TokenPurpose, UserRole

# Configure logging
logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request processing"""
    
    def __init__(self, app, auth_service: AuthenticationService):
        super().__init__(app)
        self.auth_service = auth_service
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware"""
        start_time = time.time()
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log successful request
            process_time = time.time() - start_time
            await self.audit_logger.log_request(
                request, response, client_ip, user_agent, process_time
            )
            
            return response
            
        except HTTPException as e:
            # Log failed request
            process_time = time.time() - start_time
            await self.audit_logger.log_error(
                request, e, client_ip, user_agent, process_time
            )
            raise
        
        except Exception as e:
            # Log unexpected error
            process_time = time.time() - start_time
            await self.audit_logger.log_error(
                request, e, client_ip, user_agent, process_time
            )
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
        self.max_requests = 100  # per minute
        self.window_seconds = 60
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for client IP"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[client_ip].append(now)
        return True

class AuditLogger:
    """Audit logging for security events"""
    
    async def log_request(self, request: Request, response: Response, 
                         client_ip: str, user_agent: str, process_time: float):
        """Log successful request"""
        log_entry = {
            "timestamp": time.time(),
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "status_code": response.status_code,
            "process_time": process_time,
            "user_id": getattr(request.state, "user_id", None),
            "session_id": getattr(request.state, "session_id", None)
        }
        
        logger.info(f"Request processed: {json.dumps(log_entry)}")
    
    async def log_error(self, request: Request, error: Exception, 
                       client_ip: str, user_agent: str, process_time: float):
        """Log request error"""
        log_entry = {
            "timestamp": time.time(),
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "process_time": process_time,
            "user_id": getattr(request.state, "user_id", None),
            "session_id": getattr(request.state, "session_id", None)
        }
        
        logger.error(f"Request error: {json.dumps(log_entry)}")

class AuthenticationDependency:
    """Dependency for authentication"""
    
    def __init__(self, auth_service: AuthenticationService):
        self.auth_service = auth_service
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request, 
                      credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Authenticate request"""
        token = credentials.credentials
        
        try:
            # Verify token (without purpose check for general auth)
            claims = self.auth_service.jwt_manager.verify_token(token)
            
            # Store user info in request state
            request.state.user_id = claims.user_id
            request.state.username = claims.username
            request.state.role = claims.role
            request.state.jurisdiction = claims.jurisdiction
            request.state.purpose = claims.purpose
            request.state.session_id = claims.session_id
            
            return claims
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")

class PurposeBindingDependency:
    """Dependency for purpose-bound authentication"""
    
    def __init__(self, auth_service: AuthenticationService, required_purpose: TokenPurpose):
        self.auth_service = auth_service
        self.required_purpose = required_purpose
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request,
                      credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Authenticate with purpose binding"""
        token = credentials.credentials
        
        try:
            # Verify token with purpose check
            claims = self.auth_service.jwt_manager.verify_token(token, self.required_purpose)
            
            # Store user info in request state
            request.state.user_id = claims.user_id
            request.state.username = claims.username
            request.state.role = claims.role
            request.state.jurisdiction = claims.jurisdiction
            request.state.purpose = claims.purpose
            request.state.session_id = claims.session_id
            
            return claims
            
        except ValueError as e:
            raise HTTPException(status_code=403, detail=f"Purpose binding failed: {e}")

class RoleBasedDependency:
    """Dependency for role-based authorization"""
    
    def __init__(self, auth_service: AuthenticationService, required_roles: list):
        self.auth_service = auth_service
        self.required_roles = [role.value if isinstance(role, UserRole) else role for role in required_roles]
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request,
                      credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Authorize based on role"""
        token = credentials.credentials
        
        try:
            # Verify token
            claims = self.auth_service.jwt_manager.verify_token(token)
            
            # Check role
            if claims.role not in self.required_roles:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Role '{claims.role}' not authorized. Required: {self.required_roles}"
                )
            
            # Store user info in request state
            request.state.user_id = claims.user_id
            request.state.username = claims.username
            request.state.role = claims.role
            request.state.jurisdiction = claims.jurisdiction
            request.state.purpose = claims.purpose
            request.state.session_id = claims.session_id
            
            return claims
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")

class PermissionDependency:
    """Dependency for permission-based authorization"""
    
    def __init__(self, auth_service: AuthenticationService, required_permissions: list):
        self.auth_service = auth_service
        self.required_permissions = required_permissions
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request,
                      credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Authorize based on permissions"""
        token = credentials.credentials
        
        try:
            # Verify token
            claims = self.auth_service.jwt_manager.verify_token(token)
            
            # Check permissions
            user_role = UserRole(claims.role)
            has_permission = any(
                self.auth_service.rbac.has_permission(user_role, perm) 
                for perm in self.required_permissions
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {self.required_permissions}"
                )
            
            # Store user info in request state
            request.state.user_id = claims.user_id
            request.state.username = claims.username
            request.state.role = claims.role
            request.state.jurisdiction = claims.jurisdiction
            request.state.purpose = claims.purpose
            request.state.session_id = claims.session_id
            
            return claims
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")

def setup_security_middleware(app: FastAPI, auth_service: AuthenticationService):
    """Setup security middleware for FastAPI app"""
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware, auth_service=auth_service)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://takedown-frontend.gov", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["takedown-backend.gov", "api.takedown-backend.gov", "localhost"]
    )
    
    return app

# Dependency factories for common use cases
def require_victim_auth(auth_service: AuthenticationService):
    """Require victim authentication with takedown submission purpose"""
    return PurposeBindingDependency(auth_service, TokenPurpose.TAKEDOWN_SUBMISSION)

def require_officer_auth(auth_service: AuthenticationService):
    """Require officer authentication with case review purpose"""
    return PurposeBindingDependency(auth_service, TokenPurpose.CASE_REVIEW)

def require_admin_auth(auth_service: AuthenticationService):
    """Require admin authentication with admin action purpose"""
    return PurposeBindingDependency(auth_service, TokenPurpose.ADMIN_ACTION)

def require_any_auth(auth_service: AuthenticationService):
    """Require any valid authentication"""
    return AuthenticationDependency(auth_service)

def require_officer_or_admin(auth_service: AuthenticationService):
    """Require officer or admin role"""
    return RoleBasedDependency(auth_service, [UserRole.OFFICER, UserRole.ADMIN])

def require_case_review_permission(auth_service: AuthenticationService):
    """Require case review permission"""
    return PermissionDependency(auth_service, ["review_case", "approve_case", "reject_case"])

def require_report_generation_permission(auth_service: AuthenticationService):
    """Require report generation permission"""
    return PermissionDependency(auth_service, ["generate_reports"])

# Example usage in FastAPI routes
def example_fastapi_routes():
    """Example FastAPI route definitions with security"""
    from fastapi import FastAPI
    
    app = FastAPI()
    config = SecurityConfig()
    auth_service = AuthenticationService(config)
    
    # Setup security middleware
    setup_security_middleware(app, auth_service)
    
    # Example routes with different security requirements
    
    @app.post("/auth/login")
    async def login(request: dict):
        """Public login endpoint"""
        # Implementation here
        pass
    
    @app.post("/cases/submit")
    async def submit_case(
        request: dict,
        auth: dict = Depends(require_victim_auth(auth_service))
    ):
        """Victim-only case submission"""
        # Implementation here
        pass
    
    @app.patch("/cases/{case_id}")
    async def update_case(
        case_id: str,
        request: dict,
        auth: dict = Depends(require_officer_auth(auth_service))
    ):
        """Officer-only case updates"""
        # Implementation here
        pass
    
    @app.get("/admin/metrics")
    async def get_metrics(
        auth: dict = Depends(require_admin_auth(auth_service))
    ):
        """Admin-only metrics"""
        # Implementation here
        pass
    
    @app.get("/reports/cases")
    async def generate_report(
        auth: dict = Depends(require_report_generation_permission(auth_service))
    ):
        """Permission-based report generation"""
        # Implementation here
        pass
    
    return app

if __name__ == "__main__":
    # Example usage
    print("=== Security Middleware Example ===")
    
    # Initialize security components
    config = SecurityConfig()
    auth_service = AuthenticationService(config)
    
    # Create example FastAPI app
    app = example_fastapi_routes()
    
    print("✅ Security middleware configured")
    print("✅ Authentication dependencies created")
    print("✅ Role-based access control enabled")
    print("✅ Purpose-binding JWT implemented")
    print("✅ Rate limiting configured")
    print("✅ Audit logging enabled")

