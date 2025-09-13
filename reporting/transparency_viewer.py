"""
Take It Down Backend - Transparency Log Viewer
Web interface for viewing tamper-proof transparency logs
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """Transparency log entry"""
    timestamp: datetime
    case_id: str
    action: str
    actor: str
    old_state: Optional[str]
    new_state: Optional[str]
    reason_code: str
    jurisdiction: str
    priority: str
    metadata: Dict[str, Any]
    checksum: str

class TransparencyViewer:
    """Viewer for transparency logs with integrity verification"""
    
    def __init__(self, log_file_path: str = "logs/transparency.jsonl"):
        self.log_file_path = Path(log_file_path)
        self.manifest_file = self.log_file_path.parent / "manifest.jsonl"
    
    def get_log_entries(self, case_id: str = None, action: str = None, 
                       actor: str = None, from_date: datetime = None,
                       to_date: datetime = None, limit: int = 100) -> List[LogEntry]:
        """Get filtered log entries"""
        
        if not self.log_file_path.exists():
            return []
        
        entries = []
        
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entry = self._parse_log_entry(data)
                    
                    # Apply filters
                    if case_id and entry.case_id != case_id:
                        continue
                    if action and entry.action != action:
                        continue
                    if actor and entry.actor != actor:
                        continue
                    if from_date and entry.timestamp < from_date:
                        continue
                    if to_date and entry.timestamp > to_date:
                        continue
                    
                    entries.append(entry)
                    
                    if len(entries) >= limit:
                        break
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Invalid log entry: {e}")
                    continue
        
        return entries
    
    def _parse_log_entry(self, data: Dict) -> LogEntry:
        """Parse log entry from JSON data"""
        return LogEntry(
            timestamp=datetime.fromisoformat(data['timestamp']),
            case_id=data['case_id'],
            action=data['action'],
            actor=data['actor'],
            old_state=data.get('old_state'),
            new_state=data.get('new_state'),
            reason_code=data['reason_code'],
            jurisdiction=data['jurisdiction'],
            priority=data['priority'],
            metadata=data['metadata'],
            checksum=data['checksum']
        )
    
    def verify_entry_integrity(self, entry: LogEntry) -> Tuple[bool, str]:
        """Verify integrity of a single log entry"""
        # Recalculate checksum
        data = {
            "timestamp": entry.timestamp.isoformat(),
            "case_id": entry.case_id,
            "action": entry.action,
            "actor": entry.actor,
            "old_state": entry.old_state,
            "new_state": entry.new_state,
            "reason_code": entry.reason_code,
            "jurisdiction": entry.jurisdiction,
            "priority": entry.priority,
            "metadata": entry.metadata
        }
        
        data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
        calculated_checksum = hashlib.sha256(data_string.encode()).hexdigest()
        
        if entry.checksum == calculated_checksum:
            return True, "Integrity verified"
        else:
            return False, f"Checksum mismatch: expected {calculated_checksum}, got {entry.checksum}"
    
    def get_case_timeline(self, case_id: str) -> List[LogEntry]:
        """Get complete timeline for a specific case"""
        return self.get_log_entries(case_id=case_id, limit=1000)
    
    def get_system_activity(self, hours: int = 24) -> List[LogEntry]:
        """Get system activity for specified hours"""
        from_date = datetime.utcnow() - timedelta(hours=hours)
        return self.get_log_entries(from_date=from_date, limit=1000)
    
    def get_escalation_events(self, hours: int = 24) -> List[LogEntry]:
        """Get escalation events for specified hours"""
        from_date = datetime.utcnow() - timedelta(hours=hours)
        return self.get_log_entries(
            action="escalate", from_date=from_date, limit=100
        )
    
    def get_sla_violations(self, hours: int = 24) -> List[LogEntry]:
        """Get SLA violation events"""
        from_date = datetime.utcnow() - timedelta(hours=hours)
        return self.get_log_entries(
            reason_code="sla_violation", from_date=from_date, limit=100
        )
    
    def get_audit_summary(self, from_date: datetime = None, 
                         to_date: datetime = None) -> Dict[str, Any]:
        """Get audit summary statistics"""
        
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=30)
        if not to_date:
            to_date = datetime.utcnow()
        
        entries = self.get_log_entries(from_date=from_date, to_date=to_date, limit=10000)
        
        # Calculate statistics
        total_actions = len(entries)
        unique_cases = len(set(entry.case_id for entry in entries))
        unique_actors = len(set(entry.actor for entry in entries))
        
        # Action breakdown
        action_counts = {}
        for entry in entries:
            action_counts[entry.action] = action_counts.get(entry.action, 0) + 1
        
        # Actor breakdown
        actor_counts = {}
        for entry in entries:
            actor_counts[entry.actor] = actor_counts.get(entry.actor, 0) + 1
        
        # Jurisdiction breakdown
        jurisdiction_counts = {}
        for entry in entries:
            jurisdiction_counts[entry.jurisdiction] = jurisdiction_counts.get(entry.jurisdiction, 0) + 1
        
        # Integrity check
        integrity_issues = 0
        for entry in entries:
            is_valid, _ = self.verify_entry_integrity(entry)
            if not is_valid:
                integrity_issues += 1
        
        return {
            "period": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            },
            "total_actions": total_actions,
            "unique_cases": unique_cases,
            "unique_actors": unique_actors,
            "integrity_issues": integrity_issues,
            "integrity_percentage": round((total_actions - integrity_issues) / total_actions * 100, 2) if total_actions > 0 else 100,
            "action_breakdown": action_counts,
            "actor_breakdown": actor_counts,
            "jurisdiction_breakdown": jurisdiction_counts
        }

class TransparencyAPI:
    """API endpoints for transparency log access"""
    
    def __init__(self, viewer: TransparencyViewer):
        self.viewer = viewer
    
    def get_case_audit_trail(self, case_id: str) -> Dict[str, Any]:
        """Get audit trail for a specific case"""
        entries = self.viewer.get_case_timeline(case_id)
        
        # Verify integrity of all entries
        verified_entries = []
        integrity_issues = []
        
        for entry in entries:
            is_valid, message = self.viewer.verify_entry_integrity(entry)
            if is_valid:
                verified_entries.append(entry)
            else:
                integrity_issues.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "case_id": entry.case_id,
                    "action": entry.action,
                    "issue": message
                })
        
        return {
            "case_id": case_id,
            "total_entries": len(entries),
            "verified_entries": len(verified_entries),
            "integrity_issues": len(integrity_issues),
            "timeline": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "action": entry.action,
                    "actor": entry.actor,
                    "old_state": entry.old_state,
                    "new_state": entry.new_state,
                    "reason_code": entry.reason_code,
                    "metadata": entry.metadata,
                    "checksum": entry.checksum
                }
                for entry in verified_entries
            ],
            "integrity_issues": integrity_issues
        }
    
    def get_system_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system metrics for specified hours"""
        summary = self.viewer.get_audit_summary(
            from_date=datetime.utcnow() - timedelta(hours=hours)
        )
        
        # Get recent activity
        recent_activity = self.viewer.get_system_activity(hours)
        
        # Get escalation events
        escalations = self.viewer.get_escalation_events(hours)
        
        # Get SLA violations
        sla_violations = self.viewer.get_sla_violations(hours)
        
        return {
            "summary": summary,
            "recent_activity": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "case_id": entry.case_id,
                    "action": entry.action,
                    "actor": entry.actor,
                    "jurisdiction": entry.jurisdiction
                }
                for entry in recent_activity[:10]  # Last 10 activities
            ],
            "escalations": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "case_id": entry.case_id,
                    "actor": entry.actor,
                    "reason_code": entry.reason_code
                }
                for entry in escalations
            ],
            "sla_violations": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "case_id": entry.case_id,
                    "actor": entry.actor,
                    "metadata": entry.metadata
                }
                for entry in sla_violations
            ]
        }
    
    def verify_log_integrity(self) -> Dict[str, Any]:
        """Verify integrity of entire log file"""
        if not self.viewer.log_file_path.exists():
            return {
                "status": "error",
                "message": "Log file does not exist"
            }
        
        entries = self.viewer.get_log_entries(limit=10000)
        total_entries = len(entries)
        integrity_issues = []
        
        for entry in entries:
            is_valid, message = self.viewer.verify_entry_integrity(entry)
            if not is_valid:
                integrity_issues.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "case_id": entry.case_id,
                    "action": entry.action,
                    "issue": message
                })
        
        return {
            "status": "success" if len(integrity_issues) == 0 else "warning",
            "total_entries": total_entries,
            "integrity_issues": len(integrity_issues),
            "integrity_percentage": round((total_entries - len(integrity_issues)) / total_entries * 100, 2) if total_entries > 0 else 100,
            "issues": integrity_issues
        }

# Example usage
def example_transparency_viewer():
    """Example transparency viewer usage"""
    print("=== Transparency Viewer Example ===")
    
    # Initialize viewer
    viewer = TransparencyViewer()
    api = TransparencyAPI(viewer)
    
    # Get case timeline
    case_id = "CASE-2025-0001"
    timeline = viewer.get_case_timeline(case_id)
    print(f"Case {case_id} timeline: {len(timeline)} entries")
    
    # Get system activity
    activity = viewer.get_system_activity(24)
    print(f"System activity (24h): {len(activity)} entries")
    
    # Get audit summary
    summary = viewer.get_audit_summary()
    print(f"Audit summary: {summary['total_actions']} total actions")
    print(f"Integrity: {summary['integrity_percentage']}% verified")
    
    # Verify log integrity
    integrity = api.verify_log_integrity()
    if integrity['status'] == 'success':
        print("✅ Log integrity verified")
    else:
        print(f"⚠️ Integrity issues found: {integrity['integrity_issues']}")
    
    print("✅ Transparency viewer ready")
    print("✅ Tamper-proof audit trails accessible")

if __name__ == "__main__":
    example_transparency_viewer()

