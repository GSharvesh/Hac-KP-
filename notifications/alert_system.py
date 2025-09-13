"""
Take It Down Backend - Notification & Alert System
Multi-channel notifications with severity-based routing
"""

import asyncio
import json
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class NotificationSeverity(Enum):
    """Notification severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    PUSH = "push"

class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class NotificationTemplate:
    """Notification template structure"""
    template_id: str
    notification_type: str
    severity: NotificationSeverity
    channels: List[NotificationChannel]
    subject_template: str
    message_template: str
    variables: List[str]

@dataclass
class NotificationRequest:
    """Notification request structure"""
    notification_id: str
    case_id: str
    recipient_id: str
    notification_type: str
    severity: NotificationSeverity
    title: str
    message: str
    channels: List[NotificationChannel]
    metadata: Dict[str, Any]
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

@dataclass
class NotificationDelivery:
    """Notification delivery record"""
    delivery_id: str
    notification_id: str
    channel: NotificationChannel
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class NotificationTemplates:
    """Predefined notification templates"""
    
    TEMPLATES = {
        "case_submitted": NotificationTemplate(
            template_id="case_submitted",
            notification_type="case_submitted",
            severity=NotificationSeverity.MEDIUM,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            subject_template="New Takedown Case Submitted - {case_ref}",
            message_template="A new takedown case {case_ref} has been submitted by {submitter_name} in {jurisdiction}.",
            variables=["case_ref", "submitter_name", "jurisdiction"]
        ),
        
        "case_assigned": NotificationTemplate(
            template_id="case_assigned",
            notification_type="case_assigned",
            severity=NotificationSeverity.MEDIUM,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            subject_template="Case Assigned - {case_ref}",
            message_template="Case {case_ref} has been assigned to you for review. Priority: {priority}",
            variables=["case_ref", "priority"]
        ),
        
        "case_escalated": NotificationTemplate(
            template_id="case_escalated",
            notification_type="case_escalated",
            severity=NotificationSeverity.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK],
            subject_template="URGENT: Case Escalated - {case_ref}",
            message_template="Case {case_ref} has been escalated to level {escalation_level} due to SLA violation. Immediate action required.",
            variables=["case_ref", "escalation_level"]
        ),
        
        "sla_warning": NotificationTemplate(
            template_id="sla_warning",
            notification_type="sla_warning",
            severity=NotificationSeverity.MEDIUM,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            subject_template="SLA Warning - {case_ref}",
            message_template="Case {case_ref} SLA expires in {hours_remaining} hours. Please review promptly.",
            variables=["case_ref", "hours_remaining"]
        ),
        
        "case_approved": NotificationTemplate(
            template_id="case_approved",
            notification_type="case_approved",
            severity=NotificationSeverity.LOW,
            channels=[NotificationChannel.EMAIL],
            subject_template="Case Approved - {case_ref}",
            message_template="Your case {case_ref} has been approved and action has been taken.",
            variables=["case_ref"]
        ),
        
        "case_rejected": NotificationTemplate(
            template_id="case_rejected",
            notification_type="case_rejected",
            severity=NotificationSeverity.LOW,
            channels=[NotificationChannel.EMAIL],
            subject_template="Case Rejected - {case_ref}",
            message_template="Your case {case_ref} has been rejected. Reason: {reason}",
            variables=["case_ref", "reason"]
        ),
        
        "system_alert": NotificationTemplate(
            template_id="system_alert",
            notification_type="system_alert",
            severity=NotificationSeverity.CRITICAL,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.WEBHOOK],
            subject_template="CRITICAL: System Alert - {alert_type}",
            message_template="System alert: {alert_message}. Time: {timestamp}",
            variables=["alert_type", "alert_message", "timestamp"]
        )
    }

class ChannelProvider:
    """Base class for notification channel providers"""
    
    async def send(self, notification: NotificationRequest, message: str) -> Tuple[bool, str]:
        """Send notification via this channel"""
        raise NotImplementedError

class EmailProvider(ChannelProvider):
    """Email notification provider"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(self, notification: NotificationRequest, message: str) -> Tuple[bool, str]:
        """Send email notification"""
        try:
            # Get recipient email (mock implementation)
            recipient_email = await self._get_recipient_email(notification.recipient_id)
            if not recipient_email:
                return False, "Recipient email not found"
            
            # Create email
            email_message = f"""
            Subject: {notification.title}
            To: {recipient_email}
            From: Take It Down System <noreply@takedown-backend.gov>
            
            {message}
            
            ---
            This is an automated message from the Take It Down system.
            """
            
            # Send email (mock implementation)
            logger.info(f"Email sent to {recipient_email}: {notification.title}")
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False, str(e)
    
    async def _get_recipient_email(self, recipient_id: str) -> Optional[str]:
        """Get recipient email address"""
        # Mock implementation - in production, query database
        mock_emails = {
            "victim_001": "jane.doe@example.com",
            "officer_001": "alex.brown@law.gov",
            "admin_001": "mike.chen@admin.gov"
        }
        return mock_emails.get(recipient_id)

class SMSProvider(ChannelProvider):
    """SMS notification provider"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def send(self, notification: NotificationRequest, message: str) -> Tuple[bool, str]:
        """Send SMS notification"""
        try:
            # Get recipient phone number (mock implementation)
            phone_number = await self._get_recipient_phone(notification.recipient_id)
            if not phone_number:
                return False, "Recipient phone number not found"
            
            # Send SMS (mock implementation)
            logger.info(f"SMS sent to {phone_number}: {message[:50]}...")
            return True, "SMS sent successfully"
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return False, str(e)
    
    async def _get_recipient_phone(self, recipient_id: str) -> Optional[str]:
        """Get recipient phone number"""
        # Mock implementation - in production, query database
        mock_phones = {
            "officer_001": "+1234567890",
            "admin_001": "+1234567891"
        }
        return mock_phones.get(recipient_id)

class WebhookProvider(ChannelProvider):
    """Webhook notification provider"""
    
    def __init__(self, webhook_url: str, secret: str = None):
        self.webhook_url = webhook_url
        self.secret = secret
    
    async def send(self, notification: NotificationRequest, message: str) -> Tuple[bool, str]:
        """Send webhook notification"""
        try:
            payload = {
                "notification_id": notification.notification_id,
                "case_id": notification.case_id,
                "type": notification.notification_type,
                "severity": notification.severity.value,
                "title": notification.title,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": notification.metadata
            }
            
            headers = {"Content-Type": "application/json"}
            if self.secret:
                headers["X-Webhook-Secret"] = self.secret
            
            # Send webhook (mock implementation)
            logger.info(f"Webhook sent to {self.webhook_url}: {notification.title}")
            return True, "Webhook sent successfully"
            
        except Exception as e:
            logger.error(f"Webhook sending failed: {e}")
            return False, str(e)

class SlackProvider(ChannelProvider):
    """Slack notification provider"""
    
    def __init__(self, webhook_url: str, channel: str = "#takedown-alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def send(self, notification: NotificationRequest, message: str) -> Tuple[bool, str]:
        """Send Slack notification"""
        try:
            # Determine color based on severity
            color_map = {
                NotificationSeverity.LOW: "good",
                NotificationSeverity.MEDIUM: "warning",
                NotificationSeverity.HIGH: "danger",
                NotificationSeverity.CRITICAL: "danger"
            }
            
            payload = {
                "channel": self.channel,
                "attachments": [{
                    "color": color_map.get(notification.severity, "good"),
                    "title": notification.title,
                    "text": message,
                    "fields": [
                        {"title": "Case ID", "value": notification.case_id, "short": True},
                        {"title": "Severity", "value": notification.severity.value.upper(), "short": True},
                        {"title": "Type", "value": notification.notification_type, "short": True}
                    ],
                    "footer": "Take It Down System",
                    "ts": int(datetime.utcnow().timestamp())
                }]
            }
            
            # Send to Slack (mock implementation)
            logger.info(f"Slack message sent to {self.channel}: {notification.title}")
            return True, "Slack message sent successfully"
            
        except Exception as e:
            logger.error(f"Slack sending failed: {e}")
            return False, str(e)

class NotificationService:
    """Main notification service"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.templates = NotificationTemplates.TEMPLATES
        self.providers = self._initialize_providers()
        self.delivery_queue = []
        self.retry_attempts = 3
        self.retry_delay = 300  # 5 minutes
    
    def _initialize_providers(self) -> Dict[NotificationChannel, ChannelProvider]:
        """Initialize notification providers"""
        return {
            NotificationChannel.EMAIL: EmailProvider(
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                username="noreply@takedown-backend.gov",
                password="your-email-password"
            ),
            NotificationChannel.SMS: SMSProvider(
                api_key="your-sms-api-key",
                api_secret="your-sms-api-secret"
            ),
            NotificationChannel.WEBHOOK: WebhookProvider(
                webhook_url="https://your-webhook-endpoint.com/notifications",
                secret="your-webhook-secret"
            ),
            NotificationChannel.SLACK: SlackProvider(
                webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                channel="#takedown-alerts"
            )
        }
    
    async def send_notification(self, case_id: str, recipient_id: str, 
                              notification_type: str, variables: Dict[str, Any] = None,
                              custom_channels: List[NotificationChannel] = None) -> str:
        """Send notification using template"""
        
        # Get template
        template = self.templates.get(notification_type)
        if not template:
            raise ValueError(f"Unknown notification type: {notification_type}")
        
        # Prepare variables
        variables = variables or {}
        variables.update({
            "timestamp": datetime.utcnow().isoformat(),
            "case_id": case_id
        })
        
        # Render message
        title = self._render_template(template.subject_template, variables)
        message = self._render_template(template.message_template, variables)
        
        # Determine channels
        channels = custom_channels or template.channels
        
        # Create notification request
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{case_id}"
        request = NotificationRequest(
            notification_id=notification_id,
            case_id=case_id,
            recipient_id=recipient_id,
            notification_type=notification_type,
            severity=template.severity,
            title=title,
            message=message,
            channels=channels,
            metadata=variables
        )
        
        # Send notifications
        await self._send_notification_request(request)
        
        return notification_id
    
    async def send_custom_notification(self, case_id: str, recipient_id: str,
                                     title: str, message: str, severity: NotificationSeverity,
                                     channels: List[NotificationChannel]) -> str:
        """Send custom notification"""
        
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{case_id}"
        request = NotificationRequest(
            notification_id=notification_id,
            case_id=case_id,
            recipient_id=recipient_id,
            notification_type="custom",
            severity=severity,
            title=title,
            message=message,
            channels=channels,
            metadata={}
        )
        
        await self._send_notification_request(request)
        return notification_id
    
    async def _send_notification_request(self, request: NotificationRequest):
        """Send notification request to all channels"""
        
        for channel in request.channels:
            provider = self.providers.get(channel)
            if not provider:
                logger.warning(f"No provider configured for channel: {channel}")
                continue
            
            # Create delivery record
            delivery = NotificationDelivery(
                delivery_id=f"delivery_{request.notification_id}_{channel.value}",
                notification_id=request.notification_id,
                channel=channel,
                status=NotificationStatus.PENDING
            )
            
            try:
                # Send notification
                success, message = await provider.send(request, request.message)
                
                if success:
                    delivery.status = NotificationStatus.SENT
                    delivery.sent_at = datetime.utcnow()
                    logger.info(f"Notification sent via {channel.value}: {request.title}")
                else:
                    delivery.status = NotificationStatus.FAILED
                    delivery.error_message = message
                    logger.error(f"Notification failed via {channel.value}: {message}")
                    
                    # Add to retry queue
                    if delivery.retry_count < self.retry_attempts:
                        delivery.retry_count += 1
                        self.delivery_queue.append((delivery, request))
            
            except Exception as e:
                delivery.status = NotificationStatus.FAILED
                delivery.error_message = str(e)
                logger.error(f"Notification error via {channel.value}: {e}")
            
            # Store delivery record (in production, save to database)
            await self._store_delivery_record(delivery)
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
    
    async def _store_delivery_record(self, delivery: NotificationDelivery):
        """Store delivery record in database"""
        # Mock implementation - in production, save to database
        logger.debug(f"Delivery record stored: {delivery.delivery_id}")
    
    async def process_retry_queue(self):
        """Process failed notifications for retry"""
        if not self.delivery_queue:
            return
        
        retry_items = []
        for delivery, request in self.delivery_queue:
            if delivery.retry_count < self.retry_attempts:
                retry_items.append((delivery, request))
        
        self.delivery_queue = retry_items
        
        for delivery, request in retry_items:
            await asyncio.sleep(self.retry_delay)
            await self._retry_delivery(delivery, request)
    
    async def _retry_delivery(self, delivery: NotificationDelivery, request: NotificationRequest):
        """Retry failed delivery"""
        provider = self.providers.get(delivery.channel)
        if not provider:
            return
        
        try:
            success, message = await provider.send(request, request.message)
            
            if success:
                delivery.status = NotificationStatus.SENT
                delivery.sent_at = datetime.utcnow()
                logger.info(f"Retry successful via {delivery.channel.value}")
            else:
                delivery.retry_count += 1
                delivery.error_message = message
                logger.warning(f"Retry failed via {delivery.channel.value}: {message}")
        
        except Exception as e:
            delivery.retry_count += 1
            delivery.error_message = str(e)
            logger.error(f"Retry error via {delivery.channel.value}: {e}")
        
        await self._store_delivery_record(delivery)

class SLAAlertManager:
    """SLA alert management system"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.alert_thresholds = {
            "warning_hours": 2,  # Warning 2 hours before SLA
            "critical_hours": 0,  # Critical when SLA exceeded
        }
    
    async def check_sla_alerts(self, cases: List[Dict]) -> List[str]:
        """Check cases for SLA alerts"""
        alerts_sent = []
        
        for case in cases:
            case_id = case['case_id']
            status = case['status']
            sla_due_at = case.get('sla_due_at')
            assigned_officer_id = case.get('assigned_officer_id')
            
            if not sla_due_at or status != 'In Review':
                continue
            
            now = datetime.utcnow()
            if isinstance(sla_due_at, str):
                sla_due_at = datetime.fromisoformat(sla_due_at)
            
            time_remaining = sla_due_at - now
            hours_remaining = time_remaining.total_seconds() / 3600
            
            # Check for critical alert (SLA exceeded)
            if hours_remaining <= self.alert_thresholds['critical_hours']:
                await self._send_critical_alert(case_id, assigned_officer_id, hours_remaining)
                alerts_sent.append(f"critical_alert_{case_id}")
            
            # Check for warning alert (approaching SLA)
            elif hours_remaining <= self.alert_thresholds['warning_hours']:
                await self._send_warning_alert(case_id, assigned_officer_id, hours_remaining)
                alerts_sent.append(f"warning_alert_{case_id}")
        
        return alerts_sent
    
    async def _send_critical_alert(self, case_id: str, officer_id: str, hours_overdue: float):
        """Send critical SLA alert"""
        await self.notification_service.send_notification(
            case_id=case_id,
            recipient_id=officer_id,
            notification_type="case_escalated",
            variables={
                "case_ref": case_id,
                "escalation_level": 1,
                "hours_overdue": abs(hours_overdue)
            },
            custom_channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.SLACK
            ]
        )
    
    async def _send_warning_alert(self, case_id: str, officer_id: str, hours_remaining: float):
        """Send SLA warning alert"""
        await self.notification_service.send_notification(
            case_id=case_id,
            recipient_id=officer_id,
            notification_type="sla_warning",
            variables={
                "case_ref": case_id,
                "hours_remaining": hours_remaining
            }
        )

# Example usage
async def example_notification_system():
    """Example notification system usage"""
    print("=== Notification System Example ===")
    
    # Initialize notification service
    notification_service = NotificationService()
    sla_manager = SLAAlertManager(notification_service)
    
    # Send case submission notification
    print("\n1. Sending case submission notification...")
    await notification_service.send_notification(
        case_id="CASE-2025-0001",
        recipient_id="officer_001",
        notification_type="case_submitted",
        variables={
            "case_ref": "CASE-2025-0001",
            "submitter_name": "Jane Doe",
            "jurisdiction": "IN"
        }
    )
    
    # Send SLA warning
    print("\n2. Sending SLA warning...")
    await notification_service.send_notification(
        case_id="CASE-2025-0002",
        recipient_id="officer_001",
        notification_type="sla_warning",
        variables={
            "case_ref": "CASE-2025-0002",
            "hours_remaining": 1.5
        }
    )
    
    # Send critical escalation alert
    print("\n3. Sending critical escalation alert...")
    await notification_service.send_custom_notification(
        case_id="CASE-2025-0003",
        recipient_id="admin_001",
        title="CRITICAL: System Alert",
        message="Multiple cases escalated due to SLA violations",
        severity=NotificationSeverity.CRITICAL,
        channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SMS,
            NotificationChannel.WEBHOOK
        ]
    )
    
    # Check SLA alerts for mock cases
    print("\n4. Checking SLA alerts...")
    mock_cases = [
        {
            "case_id": "CASE-2025-0004",
            "status": "In Review",
            "sla_due_at": datetime.utcnow() - timedelta(hours=1),  # Overdue
            "assigned_officer_id": "officer_001"
        },
        {
            "case_id": "CASE-2025-0005",
            "status": "In Review",
            "sla_due_at": datetime.utcnow() + timedelta(hours=1),  # Warning
            "assigned_officer_id": "officer_001"
        }
    ]
    
    alerts_sent = await sla_manager.check_sla_alerts(mock_cases)
    print(f"Alerts sent: {alerts_sent}")
    
    print("\n✅ Notification system ready")
    print("✅ Multi-channel notifications enabled")
    print("✅ Severity-based routing configured")
    print("✅ SLA alert management active")

if __name__ == "__main__":
    asyncio.run(example_notification_system())

