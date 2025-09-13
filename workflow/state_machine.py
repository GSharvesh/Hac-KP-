"""
Take It Down Backend - Workflow Engine
State machine implementation with SLA management and reason codes
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CaseStatus(Enum):
    """Case status enumeration"""
    SUBMITTED = "Submitted"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ESCALATED = "Escalated"
    CLOSED = "Closed"

class CasePriority(Enum):
    """Case priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ReasonCode(Enum):
    """Structured reason codes for state transitions"""
    # Initial submission
    INITIAL_SUBMISSION = "initial_submission"
    DUPLICATE_DETECTED = "duplicate_detected"
    
    # Review process
    OFFICER_ASSIGNMENT = "officer_assignment"
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    
    # Approval/Rejection
    CONTENT_VERIFIED_HARMFUL = "content_verified_harmful"
    CONTENT_VERIFIED_SAFE = "content_verified_safe"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FALSE_REPORT = "false_report"
    JURISDICTION_ISSUE = "jurisdiction_issue"
    
    # SLA Management
    SLA_VIOLATION = "sla_violation"
    SLA_EXTENDED = "sla_extended"
    MANUAL_ESCALATION = "manual_escalation"
    
    # System actions
    SYSTEM_ESCALATION = "system_escalation"
    CASE_CLOSED = "case_closed"
    CASE_REOPENED = "case_reopened"

@dataclass
class StateTransition:
    """Represents a state transition with metadata"""
    from_status: CaseStatus
    to_status: CaseStatus
    reason_code: ReasonCode
    required_role: str
    sla_hours: Optional[int] = None
    auto_escalation: bool = False
    description: str = ""

@dataclass
class CaseContext:
    """Context for case processing"""
    case_id: str
    current_status: CaseStatus
    priority: CasePriority
    jurisdiction: str
    submitter_id: str
    assigned_officer_id: Optional[str] = None
    escalation_level: int = 0
    sla_due_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WorkflowEngine:
    """Main workflow engine for case state management"""
    
    def __init__(self):
        self.transitions = self._define_transitions()
        self.sla_config = self._get_sla_config()
        
    def _define_transitions(self) -> Dict[Tuple[CaseStatus, str], StateTransition]:
        """Define all possible state transitions"""
        transitions = {}
        
        # Submitted -> In Review
        transitions[(CaseStatus.SUBMITTED, "start_review")] = StateTransition(
            from_status=CaseStatus.SUBMITTED,
            to_status=CaseStatus.IN_REVIEW,
            reason_code=ReasonCode.OFFICER_ASSIGNMENT,
            required_role="officer",
            sla_hours=48,
            description="Officer starts reviewing the case"
        )
        
        # In Review -> Approved
        transitions[(CaseStatus.IN_REVIEW, "approve")] = StateTransition(
            from_status=CaseStatus.IN_REVIEW,
            to_status=CaseStatus.APPROVED,
            reason_code=ReasonCode.CONTENT_VERIFIED_HARMFUL,
            required_role="officer",
            description="Officer approves the case after verification"
        )
        
        # In Review -> Rejected
        transitions[(CaseStatus.IN_REVIEW, "reject")] = StateTransition(
            from_status=CaseStatus.IN_REVIEW,
            to_status=CaseStatus.REJECTED,
            reason_code=ReasonCode.CONTENT_VERIFIED_SAFE,
            required_role="officer",
            description="Officer rejects the case as safe content"
        )
        
        # In Review -> Escalated (SLA violation)
        transitions[(CaseStatus.IN_REVIEW, "escalate")] = StateTransition(
            from_status=CaseStatus.IN_REVIEW,
            to_status=CaseStatus.ESCALATED,
            reason_code=ReasonCode.SLA_VIOLATION,
            required_role="system",
            auto_escalation=True,
            description="Case escalated due to SLA violation"
        )
        
        # Escalated -> In Review (reassigned)
        transitions[(CaseStatus.ESCALATED, "reassign")] = StateTransition(
            from_status=CaseStatus.ESCALATED,
            to_status=CaseStatus.IN_REVIEW,
            reason_code=ReasonCode.MANUAL_ESCALATION,
            required_role="admin",
            sla_hours=24,  # Shorter SLA for escalated cases
            description="Escalated case reassigned to officer"
        )
        
        # Any status -> Closed
        transitions[(CaseStatus.APPROVED, "close")] = StateTransition(
            from_status=CaseStatus.APPROVED,
            to_status=CaseStatus.CLOSED,
            reason_code=ReasonCode.CASE_CLOSED,
            required_role="officer",
            description="Case closed after successful resolution"
        )
        
        transitions[(CaseStatus.REJECTED, "close")] = StateTransition(
            from_status=CaseStatus.REJECTED,
            to_status=CaseStatus.CLOSED,
            reason_code=ReasonCode.CASE_CLOSED,
            required_role="officer",
            description="Case closed after rejection"
        )
        
        return transitions
    
    def _get_sla_config(self) -> Dict[CasePriority, int]:
        """Get SLA configuration by priority"""
        return {
            CasePriority.LOW: 72,      # 3 days
            CasePriority.MEDIUM: 48,   # 2 days
            CasePriority.HIGH: 24,     # 1 day
            CasePriority.URGENT: 12    # 12 hours
        }
    
    def can_transition(self, context: CaseContext, action: str, user_role: str) -> Tuple[bool, str]:
        """Check if a state transition is allowed"""
        key = (context.current_status, action)
        
        if key not in self.transitions:
            return False, f"Invalid transition from {context.current_status.value} with action '{action}'"
        
        transition = self.transitions[key]
        
        # Check role permissions
        if transition.required_role != "system" and user_role != transition.required_role:
            return False, f"Role '{user_role}' not allowed for this action. Required: {transition.required_role}"
        
        # Check if case is already in target state
        if context.current_status == transition.to_status:
            return False, f"Case is already in {transition.to_status.value} status"
        
        return True, "Transition allowed"
    
    def execute_transition(self, context: CaseContext, action: str, user_id: str, 
                         user_role: str, notes: str = None) -> Tuple[bool, str, StateTransition]:
        """Execute a state transition"""
        can_transition, error_msg = self.can_transition(context, action, user_role)
        
        if not can_transition:
            return False, error_msg, None
        
        transition = self.transitions[(context.current_status, action)]
        
        # Calculate new SLA due date
        new_sla_due_at = None
        if transition.sla_hours:
            new_sla_due_at = datetime.now() + timedelta(hours=transition.sla_hours)
        
        # Update context
        context.current_status = transition.to_status
        context.updated_at = datetime.now()
        
        if transition.sla_hours:
            context.sla_due_at = new_sla_due_at
        
        if transition.auto_escalation:
            context.escalation_level += 1
        
        logger.info(f"Case {context.case_id} transitioned: {transition.from_status.value} -> {transition.to_status.value} ({transition.reason_code.value})")
        
        return True, "Transition successful", transition
    
    def get_available_actions(self, context: CaseContext, user_role: str) -> List[str]:
        """Get available actions for current state and user role"""
        available_actions = []
        
        for (from_status, action), transition in self.transitions.items():
            if (from_status == context.current_status and 
                (transition.required_role == "system" or transition.required_role == user_role)):
                available_actions.append(action)
        
        return available_actions
    
    def get_sla_status(self, context: CaseContext) -> str:
        """Get SLA status for a case"""
        if not context.sla_due_at:
            return "no_sla"
        
        now = datetime.now()
        time_remaining = context.sla_due_at - now
        
        if time_remaining.total_seconds() <= 0:
            return "overdue"
        elif time_remaining.total_seconds() <= 2 * 3600:  # 2 hours
            return "near_due"
        else:
            return "on_time"
    
    def should_escalate(self, context: CaseContext) -> bool:
        """Check if case should be escalated due to SLA violation"""
        if context.current_status != CaseStatus.IN_REVIEW:
            return False
        
        if not context.sla_due_at:
            return False
        
        return datetime.now() > context.sla_due_at

class SLAProcessor:
    """Background processor for SLA management"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow = workflow_engine
        self.logger = logging.getLogger(__name__ + ".SLAProcessor")
    
    def process_sla_violations(self, cases: List[CaseContext]) -> List[Dict]:
        """Process SLA violations and escalate cases"""
        escalated_cases = []
        
        for case in cases:
            if self.workflow.should_escalate(case):
                success, message, transition = self.workflow.execute_transition(
                    case, "escalate", "system", "system", 
                    f"Auto-escalated due to SLA violation (level {case.escalation_level + 1})"
                )
                
                if success:
                    escalated_cases.append({
                        "case_id": case.case_id,
                        "escalation_level": case.escalation_level,
                        "sla_due_at": case.sla_due_at,
                        "transition": transition
                    })
                    self.logger.warning(f"Case {case.case_id} escalated due to SLA violation")
                else:
                    self.logger.error(f"Failed to escalate case {case.case_id}: {message}")
        
        return escalated_cases
    
    def get_cases_near_sla(self, cases: List[CaseContext], hours_threshold: int = 2) -> List[CaseContext]:
        """Get cases approaching SLA deadline"""
        near_sla_cases = []
        threshold_time = datetime.now() + timedelta(hours=hours_threshold)
        
        for case in cases:
            if (case.current_status == CaseStatus.IN_REVIEW and 
                case.sla_due_at and 
                case.sla_due_at <= threshold_time):
                near_sla_cases.append(case)
        
        return near_sla_cases

class NotificationService:
    """Service for sending notifications based on state changes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".NotificationService")
    
    def send_notification(self, case_id: str, notification_type: str, 
                         recipient_id: str, severity: str, message: str):
        """Send notification to recipient"""
        notification = {
            "case_id": case_id,
            "notification_type": notification_type,
            "recipient_id": recipient_id,
            "severity": severity,
            "message": message,
            "sent_at": datetime.now()
        }
        
        self.logger.info(f"Notification sent: {notification_type} for case {case_id} to {recipient_id}")
        # In real implementation, this would send actual notifications
        return notification
    
    def notify_case_escalation(self, case_id: str, escalation_level: int, 
                              assigned_officer_id: str):
        """Notify about case escalation"""
        message = f"Case {case_id} has been escalated to level {escalation_level}"
        return self.send_notification(
            case_id, "case_escalated", assigned_officer_id, 
            "high", message
        )
    
    def notify_sla_warning(self, case_id: str, hours_remaining: int, 
                          assigned_officer_id: str):
        """Notify about approaching SLA deadline"""
        message = f"Case {case_id} SLA expires in {hours_remaining} hours"
        return self.send_notification(
            case_id, "sla_warning", assigned_officer_id,
            "medium", message
        )

# Example usage and testing
def example_workflow():
    """Example workflow demonstration"""
    print("=== Workflow Engine Example ===")
    
    # Initialize workflow engine
    workflow = WorkflowEngine()
    
    # Create test case context
    case = CaseContext(
        case_id="CASE-2025-0001",
        current_status=CaseStatus.SUBMITTED,
        priority=CasePriority.HIGH,
        jurisdiction="IN",
        submitter_id="victim_001",
        created_at=datetime.now()
    )
    
    print(f"Initial case status: {case.current_status.value}")
    
    # Check available actions for officer
    available_actions = workflow.get_available_actions(case, "officer")
    print(f"Available actions for officer: {available_actions}")
    
    # Start review
    success, message, transition = workflow.execute_transition(
        case, "start_review", "officer_001", "officer", 
        "Starting review process"
    )
    
    if success:
        print(f"✅ {message}")
        print(f"New status: {case.current_status.value}")
        print(f"Reason code: {transition.reason_code.value}")
        print(f"SLA due at: {case.sla_due_at}")
    else:
        print(f"❌ {message}")
    
    # Check SLA status
    sla_status = workflow.get_sla_status(case)
    print(f"SLA status: {sla_status}")
    
    # Approve case
    success, message, transition = workflow.execute_transition(
        case, "approve", "officer_001", "officer",
        "Content verified as harmful"
    )
    
    if success:
        print(f"✅ {message}")
        print(f"Final status: {case.current_status.value}")
    else:
        print(f"❌ {message}")

if __name__ == "__main__":
    example_workflow()

