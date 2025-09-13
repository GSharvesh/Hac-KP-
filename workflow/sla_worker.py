"""
Take It Down Backend - SLA Background Worker
Processes SLA violations and sends notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from dataclasses import asdict

from state_machine import WorkflowEngine, CaseContext, CaseStatus, CasePriority
from database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SLAWorker:
    """Background worker for SLA processing and notifications"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.workflow = WorkflowEngine()
        self.notification_service = NotificationService()
        self.running = False
        
    async def start(self):
        """Start the SLA worker"""
        self.running = True
        logger.info("SLA Worker started")
        
        while self.running:
            try:
                await self.process_sla_cycle()
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"SLA Worker error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the SLA worker"""
        self.running = False
        logger.info("SLA Worker stopped")
    
    async def process_sla_cycle(self):
        """Process one SLA cycle"""
        logger.info("Processing SLA cycle...")
        
        # Get cases that need SLA processing
        cases = await self.get_cases_for_sla_processing()
        
        if not cases:
            logger.info("No cases need SLA processing")
            return
        
        logger.info(f"Processing {len(cases)} cases for SLA")
        
        # Process escalations
        escalated_cases = await self.process_escalations(cases)
        
        # Process warnings
        warning_cases = await self.process_sla_warnings(cases)
        
        # Log results
        if escalated_cases:
            logger.warning(f"Escalated {len(escalated_cases)} cases")
        if warning_cases:
            logger.info(f"Sent {len(warning_cases)} SLA warnings")
    
    async def get_cases_for_sla_processing(self) -> List[CaseContext]:
        """Get cases that need SLA processing"""
        query = """
        SELECT 
            c.case_id,
            c.case_ref,
            c.status,
            c.priority,
            c.jurisdiction,
            c.submitter_id,
            c.assigned_officer_id,
            c.escalation_level,
            c.sla_due_at,
            c.created_at,
            c.updated_at
        FROM cases c
        WHERE c.status IN ('In Review', 'Escalated')
        AND c.sla_due_at IS NOT NULL
        ORDER BY c.sla_due_at ASC
        """
        
        rows = await self.db.fetch_all(query)
        cases = []
        
        for row in rows:
            case = CaseContext(
                case_id=row['case_id'],
                current_status=CaseStatus(row['status']),
                priority=CasePriority(row['priority']),
                jurisdiction=row['jurisdiction'],
                submitter_id=row['submitter_id'],
                assigned_officer_id=row['assigned_officer_id'],
                escalation_level=row['escalation_level'],
                sla_due_at=row['sla_due_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            cases.append(case)
        
        return cases
    
    async def process_escalations(self, cases: List[CaseContext]) -> List[Dict]:
        """Process cases that need escalation"""
        escalated_cases = []
        
        for case in cases:
            if self.workflow.should_escalate(case):
                # Execute escalation
                success, message, transition = self.workflow.execute_transition(
                    case, "escalate", "system", "system",
                    f"Auto-escalated due to SLA violation (level {case.escalation_level})"
                )
                
                if success:
                    # Update database
                    await self.update_case_in_db(case, transition)
                    
                    # Send notifications
                    await self.send_escalation_notifications(case, transition)
                    
                    escalated_cases.append({
                        "case_id": case.case_id,
                        "escalation_level": case.escalation_level,
                        "sla_due_at": case.sla_due_at,
                        "transition": transition
                    })
                    
                    logger.warning(f"Escalated case {case.case_id} to level {case.escalation_level}")
                else:
                    logger.error(f"Failed to escalate case {case.case_id}: {message}")
        
        return escalated_cases
    
    async def process_sla_warnings(self, cases: List[CaseContext]) -> List[Dict]:
        """Process cases approaching SLA deadline"""
        warning_cases = []
        warning_threshold = datetime.now() + timedelta(hours=2)
        
        for case in cases:
            if (case.current_status == CaseStatus.IN_REVIEW and 
                case.sla_due_at and 
                case.sla_due_at <= warning_threshold and
                case.sla_due_at > datetime.now()):
                
                # Send warning notification
                hours_remaining = int((case.sla_due_at - datetime.now()).total_seconds() / 3600)
                
                if case.assigned_officer_id:
                    await self.send_sla_warning(case, hours_remaining)
                    warning_cases.append({
                        "case_id": case.case_id,
                        "hours_remaining": hours_remaining,
                        "officer_id": case.assigned_officer_id
                    })
                    
                    logger.info(f"Sent SLA warning for case {case.case_id} ({hours_remaining}h remaining)")
        
        return warning_cases
    
    async def update_case_in_db(self, case: CaseContext, transition):
        """Update case in database after state transition"""
        update_query = """
        UPDATE cases 
        SET 
            status = %s,
            escalation_level = %s,
            sla_due_at = %s,
            updated_at = %s
        WHERE case_id = %s
        """
        
        await self.db.execute(update_query, (
            case.current_status.value,
            case.escalation_level,
            case.sla_due_at,
            case.updated_at,
            case.case_id
        ))
        
        # Insert audit log
        audit_query = """
        INSERT INTO audit_logs (
            case_id, actor_id, action, old_state, new_state, 
            reason_code, meta, created_at, checksum
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        meta = {
            "escalation_level": case.escalation_level,
            "sla_due_at": case.sla_due_at.isoformat() if case.sla_due_at else None,
            "auto_escalation": True
        }
        
        checksum = self.calculate_audit_checksum(
            case.case_id, "system", transition.action,
            transition.from_status.value, transition.to_status.value,
            datetime.now()
        )
        
        await self.db.execute(audit_query, (
            case.case_id,
            "system",
            transition.action,
            transition.from_status.value,
            transition.to_status.value,
            transition.reason_code.value,
            json.dumps(meta),
            datetime.now(),
            checksum
        ))
    
    async def send_escalation_notifications(self, case: CaseContext, transition):
        """Send notifications for case escalation"""
        # Notify assigned officer
        if case.assigned_officer_id:
            message = f"Case {case.case_id} has been escalated to level {case.escalation_level} due to SLA violation"
            await self.notification_service.send_notification(
                case.case_id, "case_escalated", case.assigned_officer_id,
                "high", message
            )
        
        # Notify admins
        admin_query = "SELECT user_id FROM users WHERE role = 'admin' AND is_active = true"
        admins = await self.db.fetch_all(admin_query)
        
        for admin in admins:
            message = f"Case {case.case_id} escalated to level {case.escalation_level} - requires attention"
            await self.notification_service.send_notification(
                case.case_id, "admin_escalation_alert", admin['user_id'],
                "critical", message
            )
    
    async def send_sla_warning(self, case: CaseContext, hours_remaining: int):
        """Send SLA warning notification"""
        message = f"Case {case.case_id} SLA expires in {hours_remaining} hours"
        await self.notification_service.send_notification(
            case.case_id, "sla_warning", case.assigned_officer_id,
            "medium", message
        )
    
    def calculate_audit_checksum(self, case_id: str, actor_id: str, action: str,
                               old_state: str, new_state: str, created_at: datetime) -> str:
        """Calculate audit log checksum for integrity verification"""
        import hashlib
        
        data = f"{case_id}{actor_id}{action}{old_state}{new_state}{created_at.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

class NotificationService:
    """Notification service for sending alerts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".NotificationService")
    
    async def send_notification(self, case_id: str, notification_type: str,
                               recipient_id: str, severity: str, message: str):
        """Send notification to recipient"""
        # In a real implementation, this would integrate with:
        # - Email service (SendGrid, AWS SES)
        # - SMS service (Twilio)
        # - Push notifications
        # - Webhook endpoints
        # - Discord/Slack bots
        
        notification = {
            "case_id": case_id,
            "notification_type": notification_type,
            "recipient_id": recipient_id,
            "severity": severity,
            "message": message,
            "sent_at": datetime.now().isoformat()
        }
        
        # Log notification (in production, this would be stored in DB)
        self.logger.info(f"Notification sent: {json.dumps(notification)}")
        
        # Simulate different notification channels based on severity
        if severity == "critical":
            await self.send_critical_alert(notification)
        elif severity == "high":
            await self.send_high_priority_alert(notification)
        else:
            await self.send_standard_alert(notification)
    
    async def send_critical_alert(self, notification: Dict):
        """Send critical alert (immediate action required)"""
        # Send to multiple channels
        self.logger.critical(f"CRITICAL ALERT: {notification['message']}")
        # In production: email + SMS + Slack + webhook
    
    async def send_high_priority_alert(self, notification: Dict):
        """Send high priority alert"""
        self.logger.warning(f"HIGH PRIORITY: {notification['message']}")
        # In production: email + Slack
    
    async def send_standard_alert(self, notification: Dict):
        """Send standard alert"""
        self.logger.info(f"ALERT: {notification['message']}")
        # In production: email only

class DatabaseManager:
    """Mock database manager for demonstration"""
    
    async def fetch_all(self, query: str, params: tuple = None):
        """Fetch all rows from query"""
        # Mock implementation
        return []
    
    async def execute(self, query: str, params: tuple = None):
        """Execute query"""
        # Mock implementation
        pass

# Example usage
async def main():
    """Example SLA worker usage"""
    print("=== SLA Worker Example ===")
    
    # Initialize components
    db_manager = DatabaseManager()
    sla_worker = SLAWorker(db_manager)
    
    # Start worker (in production, this would run as a background service)
    print("Starting SLA worker...")
    print("Worker will process SLA violations every 5 minutes")
    print("Press Ctrl+C to stop")
    
    try:
        await sla_worker.start()
    except KeyboardInterrupt:
        print("\nStopping SLA worker...")
        sla_worker.stop()

if __name__ == "__main__":
    asyncio.run(main())

