"""
Take It Down Backend API - Example Usage
Demonstrates key API endpoints with curl commands and Python examples
"""

import requests
import json
from datetime import datetime, timedelta

# Base configuration
BASE_URL = "http://localhost:8000/v1"
API_KEY = "your-api-key-here"

# Headers for authentication
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

class TakedownAPI:
    def __init__(self, base_url=BASE_URL, api_key=API_KEY):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def login(self, username, password, purpose="takedown_submission"):
        """Login and get JWT token with purpose-binding"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": username,
                "password": password,
                "purpose": purpose
            }
        )
        if response.status_code == 200:
            token_data = response.json()
            self.headers["Authorization"] = f"Bearer {token_data['access_token']}"
            return token_data
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def submit_case(self, jurisdiction, submissions, priority="medium", notes=None):
        """Submit a new takedown case with idempotency"""
        idempotency_key = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{jurisdiction}"
        
        payload = {
            "idempotency_key": idempotency_key,
            "jurisdiction": jurisdiction,
            "priority": priority,
            "submissions": submissions,
            "notes": notes
        }
        
        response = requests.post(
            f"{self.base_url}/cases/submit",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def get_case(self, case_id):
        """Get case details"""
        response = requests.get(
            f"{self.base_url}/cases/{case_id}",
            headers=self.headers
        )
        return response.json()
    
    def update_case_status(self, case_id, action, reason_code, notes=None):
        """Update case status with reason code"""
        payload = {
            "action": action,
            "reason_code": reason_code,
            "notes": notes
        }
        
        response = requests.patch(
            f"{self.base_url}/cases/{case_id}",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def get_audit_trail(self, case_id):
        """Get case audit trail"""
        response = requests.get(
            f"{self.base_url}/audit/{case_id}",
            headers=self.headers
        )
        return response.json()
    
    def generate_report(self, from_date=None, to_date=None, jurisdiction=None, format="json"):
        """Generate compliance report"""
        params = {"format": format}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if jurisdiction:
            params["jurisdiction"] = jurisdiction
        
        response = requests.get(
            f"{self.base_url}/reports/cases",
            params=params,
            headers=self.headers
        )
        return response.json()

# Example usage scenarios
def example_victim_submission():
    """Example: Victim submits a takedown request"""
    print("=== Victim Submission Example ===")
    
    api = TakedownAPI()
    
    # Login as victim
    try:
        token_data = api.login("victim_jane_doe", "secure_password_123", "takedown_submission")
        print(f"✅ Logged in as: {token_data['user']['username']}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Submit case
    submissions = [
        {
            "kind": "URL",
            "content": "https://fake-report.com/content123"
        },
        {
            "kind": "HASH", 
            "content": "1234abcd5678efgh91011ijklmnopqrstuvwx1234abcd5678efgh91011ijklmnop"
        }
    ]
    
    try:
        result = api.submit_case(
            jurisdiction="IN",
            submissions=submissions,
            priority="high",
            notes="Reported harmful content targeting minors"
        )
        print(f"✅ Case submitted: {result['case_ref']}")
        print(f"   Status: {result['status']}")
        print(f"   Duplicate detected: {result.get('duplicate_detected', False)}")
        if result.get('origin_case_id'):
            print(f"   Origin case: {result['origin_case_id']}")
    except Exception as e:
        print(f"❌ Submission failed: {e}")

def example_officer_review():
    """Example: Officer reviews and approves a case"""
    print("\n=== Officer Review Example ===")
    
    api = TakedownAPI()
    
    # Login as officer
    try:
        token_data = api.login("officer_alex_brown", "officer_password_123", "case_review")
        print(f"✅ Logged in as: {token_data['user']['username']}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Get case details
    case_id = "650e8400-e29b-41d4-a716-446655440001"
    try:
        case = api.get_case(case_id)
        print(f"✅ Retrieved case: {case['case_ref']}")
        print(f"   Status: {case['status']}")
        print(f"   Submissions: {len(case['submissions'])}")
    except Exception as e:
        print(f"❌ Failed to get case: {e}")
        return
    
    # Start review
    try:
        result = api.update_case_status(
            case_id=case_id,
            action="start_review",
            reason_code="officer_assignment",
            notes="Starting review process"
        )
        print(f"✅ Review started: {result['status']}")
    except Exception as e:
        print(f"❌ Failed to start review: {e}")
        return
    
    # Approve case
    try:
        result = api.update_case_status(
            case_id=case_id,
            action="approve",
            reason_code="content_verified_harmful",
            notes="Content verified as harmful, action taken"
        )
        print(f"✅ Case approved: {result['status']}")
    except Exception as e:
        print(f"❌ Failed to approve case: {e}")

def example_audit_trail():
    """Example: View case audit trail"""
    print("\n=== Audit Trail Example ===")
    
    api = TakedownAPI()
    
    # Login as admin
    try:
        token_data = api.login("admin_mike_chen", "admin_password_123", "admin_action")
        print(f"✅ Logged in as: {token_data['user']['username']}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Get audit trail
    case_id = "650e8400-e29b-41d4-a716-446655440001"
    try:
        audit = api.get_audit_trail(case_id)
        print(f"✅ Audit trail for case {case_id}:")
        for log in audit['logs']:
            print(f"   {log['created_at']}: {log['action']} by {log['actor_name']}")
            print(f"     {log['old_state']} → {log['new_state']} ({log['reason_code']})")
    except Exception as e:
        print(f"❌ Failed to get audit trail: {e}")

def example_compliance_report():
    """Example: Generate compliance report"""
    print("\n=== Compliance Report Example ===")
    
    api = TakedownAPI()
    
    # Login as admin
    try:
        token_data = api.login("admin_mike_chen", "admin_password_123", "report_generation")
        print(f"✅ Logged in as: {token_data['user']['username']}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Generate report
    try:
        report = api.generate_report(
            from_date="2025-01-01",
            to_date="2025-01-31",
            jurisdiction="IN",
            format="json"
        )
        print(f"✅ Report generated: {report['report_id']}")
        print(f"   Format: {report['format']}")
        print(f"   File size: {report['file_size_bytes']} bytes")
        print(f"   Metrics:")
        metrics = report['metrics']
        print(f"     Total cases: {metrics['total_cases']}")
        print(f"     Resolved cases: {metrics['resolved_cases']}")
        print(f"     SLA violations: {metrics['sla_violations']}")
        print(f"     Compliance: {metrics['compliance_percentage']}%")
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")

# cURL examples for manual testing
def curl_examples():
    """Generate cURL commands for manual testing"""
    print("\n=== cURL Examples ===")
    
    print("1. Login:")
    print("""
curl -X POST http://localhost:8000/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "victim_jane_doe",
    "password": "secure_password_123",
    "purpose": "takedown_submission"
  }'
""")
    
    print("2. Submit case:")
    print("""
curl -X POST http://localhost:8000/v1/cases/submit \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -d '{
    "idempotency_key": "sub_20250113_001",
    "jurisdiction": "IN",
    "priority": "high",
    "submissions": [
      {
        "kind": "URL",
        "content": "https://fake-report.com/content123"
      }
    ],
    "notes": "Reported harmful content"
  }'
""")
    
    print("3. Get case details:")
    print("""
curl -X GET http://localhost:8000/v1/cases/650e8400-e29b-41d4-a716-446655440001 \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
""")
    
    print("4. Update case status:")
    print("""
curl -X PATCH http://localhost:8000/v1/cases/650e8400-e29b-41d4-a716-446655440001 \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -d '{
    "action": "approve",
    "reason_code": "content_verified_harmful",
    "notes": "Content verified as harmful"
  }'
""")
    
    print("5. Generate report:")
    print("""
curl -X GET "http://localhost:8000/v1/reports/cases?from_date=2025-01-01&to_date=2025-01-31&format=json" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
""")

if __name__ == "__main__":
    print("Take It Down Backend API Examples")
    print("=" * 50)
    
    # Run examples
    example_victim_submission()
    example_officer_review()
    example_audit_trail()
    example_compliance_report()
    curl_examples()
    
    print("\n" + "=" * 50)
    print("Examples completed! Use these patterns in your implementation.")

