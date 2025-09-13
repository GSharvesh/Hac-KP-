"""
Take It Down Backend - Authentication & Security
JWT-based authentication with purpose-binding and role-based access control
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

# Configure logging
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles enumeration"""
    VICTIM = "victim"
    OFFICER = "officer"
    ADMIN = "admin"

class TokenPurpose(Enum):
    """JWT token purpose enumeration"""
    TAKEDOWN_SUBMISSION = "takedown_submission"
    CASE_REVIEW = "case_review"
    ADMIN_ACTION = "admin_action"
    REPORT_GENERATION = "report_generation"
    SYSTEM_OPERATION = "system_operation"

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    role: UserRole
    jurisdiction: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

@dataclass
class TokenClaims:
    """JWT token claims structure"""
    user_id: str
    username: str
    role: str
    jurisdiction: str
    purpose: str
    issued_at: datetime
    expires_at: datetime
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SecurityConfig:
    """Security configuration"""
    
    def __init__(self):
        # JWT Configuration
        self.jwt_secret = self._get_or_generate_secret("JWT_SECRET")
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_hours = 24
        
        # Password Configuration
        self.password_min_length = 12
        self.password_require_special = True
        self.password_require_numbers = True
        self.password_require_uppercase = True
        
        # Rate Limiting
        self.login_attempts_max = 5
        self.login_lockout_minutes = 15
        
        # Session Management
        self.session_timeout_hours = 8
        self.max_concurrent_sessions = 3
        
        # Purpose Binding
        self.purpose_restrictions = {
            UserRole.VICTIM: [TokenPurpose.TAKEDOWN_SUBMISSION],
            UserRole.OFFICER: [TokenPurpose.CASE_REVIEW, TokenPurpose.REPORT_GENERATION],
            UserRole.ADMIN: [TokenPurpose.ADMIN_ACTION, TokenPurpose.REPORT_GENERATION, TokenPurpose.SYSTEM_OPERATION]
        }
    
    def _get_or_generate_secret(self, key: str) -> str:
        """Get secret from environment or generate new one"""
        import os
        secret = os.getenv(key)
        if not secret:
            secret = secrets.token_urlsafe(32)
            logger.warning(f"Generated new {key}. Store this securely in production!")
        return secret

class PasswordValidator:
    """Password validation and hashing"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters")
        
        if self.config.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.config.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def hash_password(self, password: str) -> str:
        """Hash password using PBKDF2"""
        import hashlib
        import os
        
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwd_hash.hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import hashlib
        
        salt = bytes.fromhex(hashed[:64])
        stored_hash = hashed[64:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == stored_hash

class JWTManager:
    """JWT token management with purpose-binding"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def create_token(self, user: User, purpose: TokenPurpose, 
                    ip_address: str = None, user_agent: str = None) -> str:
        """Create JWT token with purpose-binding"""
        
        # Validate purpose for user role
        if not self._is_purpose_allowed(user.role, purpose):
            raise ValueError(f"Purpose '{purpose.value}' not allowed for role '{user.role.value}'")
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.config.jwt_expiry_hours)
        session_id = secrets.token_urlsafe(16)
        
        claims = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "jurisdiction": user.jurisdiction,
            "purpose": purpose.value,
            "iat": now,
            "exp": expires_at,
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        token = jwt.encode(claims, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
        
        logger.info(f"Token created for user {user.username} with purpose {purpose.value}")
        return token
    
    def verify_token(self, token: str, required_purpose: TokenPurpose = None) -> TokenClaims:
        """Verify JWT token and extract claims"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm])
            
            # Extract claims
            claims = TokenClaims(
                user_id=payload["user_id"],
                username=payload["username"],
                role=payload["role"],
                jurisdiction=payload["jurisdiction"],
                purpose=payload["purpose"],
                issued_at=datetime.fromtimestamp(payload["iat"]),
                expires_at=datetime.fromtimestamp(payload["exp"]),
                session_id=payload["session_id"],
                ip_address=payload.get("ip_address"),
                user_agent=payload.get("user_agent")
            )
            
            # Verify purpose if required
            if required_purpose and claims.purpose != required_purpose.value:
                raise ValueError(f"Token purpose '{claims.purpose}' does not match required '{required_purpose.value}'")
            
            # Check if token is expired
            if claims.expires_at < datetime.utcnow():
                raise ValueError("Token has expired")
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")
    
    def _is_purpose_allowed(self, role: UserRole, purpose: TokenPurpose) -> bool:
        """Check if purpose is allowed for user role"""
        allowed_purposes = self.config.purpose_restrictions.get(role, [])
        return purpose in allowed_purposes
    
    def refresh_token(self, token: str, new_purpose: TokenPurpose = None) -> str:
        """Refresh JWT token with optional purpose change"""
        claims = self.verify_token(token)
        
        # Create new user object
        user = User(
            user_id=claims.user_id,
            username=claims.username,
            email="",  # Not needed for refresh
            role=UserRole(claims.role),
            jurisdiction=claims.jurisdiction,
            is_active=True
        )
        
        # Use same purpose or new purpose
        purpose = new_purpose or TokenPurpose(claims.purpose)
        
        return self.create_token(user, purpose, claims.ip_address, claims.user_agent)

class RoleBasedAccessControl:
    """Role-based access control system"""
    
    def __init__(self):
        self.permissions = self._define_permissions()
    
    def _define_permissions(self) -> Dict[UserRole, List[str]]:
        """Define permissions for each role"""
        return {
            UserRole.VICTIM: [
                "submit_case",
                "view_own_cases",
                "view_own_case_details"
            ],
            UserRole.OFFICER: [
                "submit_case",
                "view_own_cases",
                "view_own_case_details",
                "view_assigned_cases",
                "review_case",
                "approve_case",
                "reject_case",
                "escalate_case",
                "close_case",
                "generate_reports",
                "view_audit_logs"
            ],
            UserRole.ADMIN: [
                "submit_case",
                "view_all_cases",
                "view_case_details",
                "review_case",
                "approve_case",
                "reject_case",
                "escalate_case",
                "close_case",
                "reassign_case",
                "manage_users",
                "generate_reports",
                "view_audit_logs",
                "system_configuration",
                "view_metrics"
            ]
        }
    
    def has_permission(self, role: UserRole, permission: str) -> bool:
        """Check if role has specific permission"""
        role_permissions = self.permissions.get(role, [])
        return permission in role_permissions
    
    def get_required_permissions(self, endpoint: str) -> List[str]:
        """Get required permissions for API endpoint"""
        endpoint_permissions = {
            "POST /cases/submit": ["submit_case"],
            "GET /cases": ["view_own_cases", "view_assigned_cases", "view_all_cases"],
            "GET /cases/{id}": ["view_own_case_details", "view_case_details"],
            "PATCH /cases/{id}": ["review_case", "approve_case", "reject_case", "escalate_case", "close_case"],
            "GET /audit/{id}": ["view_audit_logs"],
            "GET /reports/cases": ["generate_reports"],
            "GET /metrics": ["view_metrics"]
        }
        
        return endpoint_permissions.get(endpoint, [])

class AuthenticationService:
    """Main authentication service"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.password_validator = PasswordValidator(config)
        self.jwt_manager = JWTManager(config)
        self.rbac = RoleBasedAccessControl()
        self.failed_attempts = {}  # In production, use Redis
    
    def authenticate_user(self, username: str, password: str, purpose: TokenPurpose,
                         ip_address: str = None, user_agent: str = None) -> Tuple[bool, str, Optional[User]]:
        """Authenticate user and return JWT token"""
        
        # Check rate limiting
        if self._is_rate_limited(username, ip_address):
            return False, "Too many failed login attempts. Please try again later.", None
        
        # Get user from database (mock implementation)
        user = self._get_user_by_username(username)
        if not user:
            self._record_failed_attempt(username, ip_address)
            return False, "Invalid username or password", None
        
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Verify password (mock implementation)
        if not self._verify_user_password(user, password):
            self._record_failed_attempt(username, ip_address)
            return False, "Invalid username or password", None
        
        # Clear failed attempts on successful login
        self._clear_failed_attempts(username, ip_address)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        # Create token
        try:
            token = self.jwt_manager.create_token(user, purpose, ip_address, user_agent)
            return True, token, user
        except ValueError as e:
            return False, str(e), None
    
    def authorize_request(self, token: str, endpoint: str, required_purpose: TokenPurpose = None) -> Tuple[bool, str, Optional[TokenClaims]]:
        """Authorize API request"""
        
        try:
            # Verify token
            claims = self.jwt_manager.verify_token(token, required_purpose)
            
            # Check permissions
            user_role = UserRole(claims.role)
            required_permissions = self.rbac.get_required_permissions(endpoint)
            
            if not required_permissions:
                return True, "No specific permissions required", claims
            
            # Check if user has any of the required permissions
            has_permission = any(
                self.rbac.has_permission(user_role, perm) for perm in required_permissions
            )
            
            if not has_permission:
                return False, f"Insufficient permissions for endpoint {endpoint}", None
            
            return True, "Authorized", claims
            
        except ValueError as e:
            return False, str(e), None
    
    def _is_rate_limited(self, username: str, ip_address: str) -> bool:
        """Check if user/IP is rate limited"""
        key = f"{username}:{ip_address}"
        attempts = self.failed_attempts.get(key, 0)
        return attempts >= self.config.login_attempts_max
    
    def _record_failed_attempt(self, username: str, ip_address: str):
        """Record failed login attempt"""
        key = f"{username}:{ip_address}"
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1
    
    def _clear_failed_attempts(self, username: str, ip_address: str):
        """Clear failed attempts on successful login"""
        key = f"{username}:{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (mock implementation)"""
        # In production, this would query the database
        mock_users = {
            "victim_jane_doe": User(
                user_id="550e8400-e29b-41d4-a716-446655440001",
                username="victim_jane_doe",
                email="jane.doe@example.com",
                role=UserRole.VICTIM,
                jurisdiction="IN",
                is_active=True
            ),
            "officer_alex_brown": User(
                user_id="550e8400-e29b-41d4-a716-446655440003",
                username="officer_alex_brown",
                email="alex.brown@law.gov",
                role=UserRole.OFFICER,
                jurisdiction="IN",
                is_active=True
            ),
            "admin_mike_chen": User(
                user_id="550e8400-e29b-41d4-a716-446655440005",
                username="admin_mike_chen",
                email="mike.chen@admin.gov",
                role=UserRole.ADMIN,
                jurisdiction="GLOBAL",
                is_active=True
            )
        }
        return mock_users.get(username)
    
    def _verify_user_password(self, user: User, password: str) -> bool:
        """Verify user password (mock implementation)"""
        # In production, this would verify against stored hash
        mock_passwords = {
            "victim_jane_doe": "secure_password_123",
            "officer_alex_brown": "officer_password_123",
            "admin_mike_chen": "admin_password_123"
        }
        return mock_passwords.get(user.username) == password

# Example usage and testing
def example_authentication():
    """Example authentication flow"""
    print("=== Authentication Example ===")
    
    # Initialize authentication service
    config = SecurityConfig()
    auth_service = AuthenticationService(config)
    
    # Test victim login
    print("\n1. Victim Login:")
    success, token, user = auth_service.authenticate_user(
        "victim_jane_doe", "secure_password_123", 
        TokenPurpose.TAKEDOWN_SUBMISSION, "192.168.1.100", "Mozilla/5.0"
    )
    
    if success:
        print(f"✅ Login successful: {user.username} ({user.role.value})")
        print(f"   Token: {token[:50]}...")
        
        # Test authorization
        print("\n2. Authorization Test:")
        authorized, message, claims = auth_service.authorize_request(
            token, "POST /cases/submit", TokenPurpose.TAKEDOWN_SUBMISSION
        )
        
        if authorized:
            print(f"✅ Authorized for case submission")
            print(f"   User: {claims.username}")
            print(f"   Purpose: {claims.purpose}")
        else:
            print(f"❌ Authorization failed: {message}")
    else:
        print(f"❌ Login failed: {token}")
    
    # Test officer login
    print("\n3. Officer Login:")
    success, token, user = auth_service.authenticate_user(
        "officer_alex_brown", "officer_password_123",
        TokenPurpose.CASE_REVIEW, "192.168.1.200", "Mozilla/5.0"
    )
    
    if success:
        print(f"✅ Login successful: {user.username} ({user.role.value})")
        
        # Test case review authorization
        authorized, message, claims = auth_service.authorize_request(
            token, "PATCH /cases/123", TokenPurpose.CASE_REVIEW
        )
        
        if authorized:
            print(f"✅ Authorized for case review")
        else:
            print(f"❌ Authorization failed: {message}")
    
    # Test purpose binding
    print("\n4. Purpose Binding Test:")
    try:
        # Try to use victim token for admin action
        success, token, user = auth_service.authenticate_user(
            "victim_jane_doe", "secure_password_123",
            TokenPurpose.ADMIN_ACTION, "192.168.1.100", "Mozilla/5.0"
        )
        print(f"❌ Should have failed: {success}")
    except ValueError as e:
        print(f"✅ Purpose binding working: {e}")

if __name__ == "__main__":
    example_authentication()

