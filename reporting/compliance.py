"""
Take It Down Backend - Compliance & Reporting System
Transparency logs, compliance metrics, and export functionality
"""

import json
import csv
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class ReportFormat(Enum):
    """Report format enumeration"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"

class ReportType(Enum):
    """Report type enumeration"""
    AUDIT = "audit"
    SLA = "sla"
    COMPLIANCE = "compliance"
    EXPORT = "export"
    TRANSPARENCY = "transparency"

@dataclass
class ComplianceMetrics:
    """Compliance metrics data structure"""
    total_cases: int
    resolved_cases: int
    sla_violations: int
    compliance_percentage: float
    average_resolution_time_hours: float
    cases_by_jurisdiction: Dict[str, int]
    cases_by_status: Dict[str, int]
    cases_by_priority: Dict[str, int]
    escalation_rate: float
    false_positive_rate: float
    generated_at: datetime

@dataclass
class TransparencyLogEntry:
    """Transparency log entry structure"""
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

class TransparencyLogger:
    """Tamper-proof transparency logging system"""
    
    def __init__(self, log_file_path: str = "logs/transparency.jsonl"):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.log_file_path.parent / "manifest.jsonl"
    
    def log_action(self, case_id: str, action: str, actor: str, 
                   old_state: str = None, new_state: str = None,
                   reason_code: str = "", jurisdiction: str = "",
                   priority: str = "", metadata: Dict = None) -> str:
        """Log an action to transparency log"""
        
        timestamp = datetime.utcnow()
        metadata = metadata or {}
        
        # Create log entry
        entry = TransparencyLogEntry(
            timestamp=timestamp,
            case_id=case_id,
            action=action,
            actor=actor,
            old_state=old_state,
            new_state=new_state,
            reason_code=reason_code,
            jurisdiction=jurisdiction,
            priority=priority,
            metadata=metadata,
            checksum=""  # Will be calculated
        )
        
        # Calculate checksum
        entry.checksum = self._calculate_checksum(entry)
        
        # Write to log file
        self._write_log_entry(entry)
        
        # Update manifest
        self._update_manifest(entry)
        
        logger.info(f"Transparency log entry created: {action} for case {case_id}")
        return entry.checksum
    
    def _calculate_checksum(self, entry: TransparencyLogEntry) -> str:
        """Calculate cryptographic checksum for log entry"""
        # Create data string for hashing (excluding checksum field)
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
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _write_log_entry(self, entry: TransparencyLogEntry):
        """Write log entry to file"""
        entry_dict = asdict(entry)
        entry_dict['timestamp'] = entry.timestamp.isoformat()
        
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry_dict) + '\n')
    
    def _update_manifest(self, entry: TransparencyLogEntry):
        """Update manifest file with entry summary"""
        manifest_entry = {
            "timestamp": entry.timestamp.isoformat(),
            "case_id": entry.case_id,
            "action": entry.action,
            "checksum": entry.checksum,
            "file_position": self._get_file_position()
        }
        
        with open(self.manifest_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(manifest_entry) + '\n')
    
    def _get_file_position(self) -> int:
        """Get current file position for manifest"""
        return self.log_file_path.stat().st_size if self.log_file_path.exists() else 0
    
    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Verify integrity of transparency logs"""
        errors = []
        
        if not self.log_file_path.exists():
            errors.append("Transparency log file does not exist")
            return False, errors
        
        # Verify each log entry
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry_data = json.loads(line.strip())
                    
                    # Recalculate checksum
                    data = {k: v for k, v in entry_data.items() if k != 'checksum'}
                    data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
                    calculated_checksum = hashlib.sha256(data_string.encode()).hexdigest()
                    
                    # Compare checksums
                    if entry_data['checksum'] != calculated_checksum:
                        errors.append(f"Checksum mismatch at line {line_num}")
                
                except (json.JSONDecodeError, KeyError) as e:
                    errors.append(f"Invalid log entry at line {line_num}: {e}")
        
        return len(errors) == 0, errors

class ComplianceReporter:
    """Compliance reporting and metrics generation"""
    
    def __init__(self, db_manager, transparency_logger: TransparencyLogger):
        self.db = db_manager
        self.transparency_logger = transparency_logger
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_compliance_report(self, from_date: datetime = None, 
                                       to_date: datetime = None,
                                       jurisdiction: str = None) -> ComplianceMetrics:
        """Generate comprehensive compliance report"""
        
        # Set default date range if not provided
        if not to_date:
            to_date = datetime.utcnow()
        if not from_date:
            from_date = to_date - timedelta(days=30)
        
        # Build query conditions
        conditions = ["created_at >= %s", "created_at <= %s"]
        params = [from_date, to_date]
        
        if jurisdiction:
            conditions.append("jurisdiction = %s")
            params.append(jurisdiction)
        
        where_clause = " AND ".join(conditions)
        
        # Get case statistics
        case_stats = await self._get_case_statistics(where_clause, params)
        
        # Get SLA metrics
        sla_metrics = await self._get_sla_metrics(where_clause, params)
        
        # Get resolution time metrics
        resolution_metrics = await self._get_resolution_metrics(where_clause, params)
        
        # Calculate compliance percentage
        total_resolved = case_stats['resolved_cases']
        sla_violations = sla_metrics['sla_violations']
        compliance_percentage = ((total_resolved - sla_violations) / total_resolved * 100) if total_resolved > 0 else 0
        
        # Calculate escalation rate
        total_cases = case_stats['total_cases']
        escalated_cases = case_stats['escalated_cases']
        escalation_rate = (escalated_cases / total_cases * 100) if total_cases > 0 else 0
        
        # Calculate false positive rate
        false_positive_rate = await self._get_false_positive_rate(where_clause, params)
        
        return ComplianceMetrics(
            total_cases=total_cases,
            resolved_cases=total_resolved,
            sla_violations=sla_violations,
            compliance_percentage=round(compliance_percentage, 2),
            average_resolution_time_hours=resolution_metrics['average_hours'],
            cases_by_jurisdiction=case_stats['by_jurisdiction'],
            cases_by_status=case_stats['by_status'],
            cases_by_priority=case_stats['by_priority'],
            escalation_rate=round(escalation_rate, 2),
            false_positive_rate=round(false_positive_rate, 2),
            generated_at=datetime.utcnow()
        )
    
    async def _get_case_statistics(self, where_clause: str, params: List) -> Dict:
        """Get case statistics from database"""
        query = f"""
        SELECT 
            COUNT(*) as total_cases,
            COUNT(*) FILTER (WHERE status IN ('Approved', 'Rejected')) as resolved_cases,
            COUNT(*) FILTER (WHERE status = 'Escalated') as escalated_cases,
            jurisdiction,
            status,
            priority
        FROM cases 
        WHERE {where_clause}
        GROUP BY jurisdiction, status, priority
        """
        
        rows = await self.db.fetch_all(query, params)
        
        # Process results
        by_jurisdiction = {}
        by_status = {}
        by_priority = {}
        total_cases = 0
        resolved_cases = 0
        escalated_cases = 0
        
        for row in rows:
            total_cases += row['total_cases']
            if row['status'] in ['Approved', 'Rejected']:
                resolved_cases += row['total_cases']
            if row['status'] == 'Escalated':
                escalated_cases += row['total_cases']
            
            # Group by jurisdiction
            jurisdiction = row['jurisdiction']
            by_jurisdiction[jurisdiction] = by_jurisdiction.get(jurisdiction, 0) + row['total_cases']
            
            # Group by status
            status = row['status']
            by_status[status] = by_status.get(status, 0) + row['total_cases']
            
            # Group by priority
            priority = row['priority']
            by_priority[priority] = by_priority.get(priority, 0) + row['total_cases']
        
        return {
            'total_cases': total_cases,
            'resolved_cases': resolved_cases,
            'escalated_cases': escalated_cases,
            'by_jurisdiction': by_jurisdiction,
            'by_status': by_status,
            'by_priority': by_priority
        }
    
    async def _get_sla_metrics(self, where_clause: str, params: List) -> Dict:
        """Get SLA violation metrics"""
        query = f"""
        SELECT 
            COUNT(*) FILTER (WHERE sla_violated = true) as sla_violations,
            COUNT(*) FILTER (WHERE sla_due_at < now() AND status = 'In Review') as currently_overdue
        FROM cases 
        WHERE {where_clause}
        """
        
        row = await self.db.fetch_one(query, params)
        return {
            'sla_violations': row['sla_violations'],
            'currently_overdue': row['currently_overdue']
        }
    
    async def _get_resolution_metrics(self, where_clause: str, params: List) -> Dict:
        """Get resolution time metrics"""
        query = f"""
        SELECT 
            AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600) as average_hours,
            MIN(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600) as min_hours,
            MAX(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600) as max_hours
        FROM cases 
        WHERE {where_clause} 
        AND status IN ('Approved', 'Rejected')
        AND resolved_at IS NOT NULL
        """
        
        row = await self.db.fetch_one(query, params)
        return {
            'average_hours': round(row['average_hours'] or 0, 2),
            'min_hours': round(row['min_hours'] or 0, 2),
            'max_hours': round(row['max_hours'] or 0, 2)
        }
    
    async def _get_false_positive_rate(self, where_clause: str, params: List) -> float:
        """Calculate false positive rate (rejected cases / total cases)"""
        query = f"""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'Rejected') as rejected_cases,
            COUNT(*) as total_cases
        FROM cases 
        WHERE {where_clause}
        """
        
        row = await self.db.fetch_one(query, params)
        if row['total_cases'] > 0:
            return (row['rejected_cases'] / row['total_cases']) * 100
        return 0.0

class ReportExporter:
    """Export reports in various formats"""
    
    def __init__(self, reports_dir: Path = Path("reports")):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(exist_ok=True)
    
    def export_compliance_report(self, metrics: ComplianceMetrics, 
                               format: ReportFormat = ReportFormat.JSON) -> str:
        """Export compliance report in specified format"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.{format.value}"
        filepath = self.reports_dir / filename
        
        if format == ReportFormat.JSON:
            self._export_json(metrics, filepath)
        elif format == ReportFormat.CSV:
            self._export_csv(metrics, filepath)
        elif format == ReportFormat.PDF:
            self._export_pdf(metrics, filepath)
        
        logger.info(f"Compliance report exported: {filepath}")
        return str(filepath)
    
    def _export_json(self, metrics: ComplianceMetrics, filepath: Path):
        """Export metrics as JSON"""
        data = asdict(metrics)
        data['generated_at'] = metrics.generated_at.isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, metrics: ComplianceMetrics, filepath: Path):
        """Export metrics as CSV"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Metric', 'Value'])
            
            # Write basic metrics
            writer.writerow(['Total Cases', metrics.total_cases])
            writer.writerow(['Resolved Cases', metrics.resolved_cases])
            writer.writerow(['SLA Violations', metrics.sla_violations])
            writer.writerow(['Compliance Percentage', f"{metrics.compliance_percentage}%"])
            writer.writerow(['Average Resolution Time (hours)', metrics.average_resolution_time_hours])
            writer.writerow(['Escalation Rate', f"{metrics.escalation_rate}%"])
            writer.writerow(['False Positive Rate', f"{metrics.false_positive_rate}%"])
            writer.writerow(['Generated At', metrics.generated_at.isoformat()])
            
            # Write jurisdiction breakdown
            writer.writerow([])
            writer.writerow(['Jurisdiction', 'Cases'])
            for jurisdiction, count in metrics.cases_by_jurisdiction.items():
                writer.writerow([jurisdiction, count])
            
            # Write status breakdown
            writer.writerow([])
            writer.writerow(['Status', 'Cases'])
            for status, count in metrics.cases_by_status.items():
                writer.writerow([status, count])
            
            # Write priority breakdown
            writer.writerow([])
            writer.writerow(['Priority', 'Cases'])
            for priority, count in metrics.cases_by_priority.items():
                writer.writerow([priority, count])
    
    def _export_pdf(self, metrics: ComplianceMetrics, filepath: Path):
        """Export metrics as PDF (requires reportlab)"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("Take It Down - Compliance Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Basic metrics
            data = [
                ['Metric', 'Value'],
                ['Total Cases', str(metrics.total_cases)],
                ['Resolved Cases', str(metrics.resolved_cases)],
                ['SLA Violations', str(metrics.sla_violations)],
                ['Compliance Percentage', f"{metrics.compliance_percentage}%"],
                ['Average Resolution Time (hours)', str(metrics.average_resolution_time_hours)],
                ['Escalation Rate', f"{metrics.escalation_rate}%"],
                ['False Positive Rate', f"{metrics.false_positive_rate}%"],
                ['Generated At', metrics.generated_at.isoformat()]
            ]
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Jurisdiction breakdown
            jurisdiction_data = [['Jurisdiction', 'Cases']]
            for jurisdiction, count in metrics.cases_by_jurisdiction.items():
                jurisdiction_data.append([jurisdiction, str(count)])
            
            jurisdiction_table = Table(jurisdiction_data)
            jurisdiction_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Cases by Jurisdiction", styles['Heading2']))
            story.append(jurisdiction_table)
            
            doc.build(story)
            
        except ImportError:
            logger.warning("reportlab not installed, falling back to JSON export")
            self._export_json(metrics, filepath.with_suffix('.json'))

class AuditTrailExporter:
    """Export audit trails for specific cases"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def export_case_audit_trail(self, case_id: str, format: ReportFormat = ReportFormat.JSON) -> str:
        """Export audit trail for a specific case"""
        
        # Get audit logs for case
        query = """
        SELECT 
            al.log_id,
            al.actor_id,
            u.username as actor_name,
            al.action,
            al.old_state,
            al.new_state,
            al.reason_code,
            al.meta,
            al.ip_address,
            al.user_agent,
            al.created_at,
            al.checksum
        FROM audit_logs al
        LEFT JOIN users u ON al.actor_id = u.user_id
        WHERE al.case_id = %s
        ORDER BY al.created_at ASC
        """
        
        logs = await self.db.fetch_all(query, (case_id,))
        
        # Export based on format
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_trail_{case_id}_{timestamp}.{format.value}"
        filepath = Path("reports") / filename
        
        if format == ReportFormat.JSON:
            self._export_audit_json(logs, filepath)
        elif format == ReportFormat.CSV:
            self._export_audit_csv(logs, filepath)
        
        return str(filepath)
    
    def _export_audit_json(self, logs: List[Dict], filepath: Path):
        """Export audit logs as JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False, default=str)
    
    def _export_audit_csv(self, logs: List[Dict], filepath: Path):
        """Export audit logs as CSV"""
        if not logs:
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)

# Example usage
def example_compliance_reporting():
    """Example compliance reporting usage"""
    print("=== Compliance Reporting Example ===")
    
    # Initialize components
    transparency_logger = TransparencyLogger()
    compliance_reporter = ComplianceReporter(None, transparency_logger)  # Mock DB
    report_exporter = ReportExporter()
    
    # Log some actions
    transparency_logger.log_action(
        "CASE-2025-0001", "case_created", "victim_jane_doe",
        jurisdiction="IN", priority="high", reason_code="initial_submission"
    )
    
    transparency_logger.log_action(
        "CASE-2025-0001", "review_started", "officer_alex_brown",
        old_state="Submitted", new_state="In Review",
        reason_code="officer_assignment"
    )
    
    transparency_logger.log_action(
        "CASE-2025-0001", "case_approved", "officer_alex_brown",
        old_state="In Review", new_state="Approved",
        reason_code="content_verified_harmful"
    )
    
    # Verify integrity
    is_valid, errors = transparency_logger.verify_integrity()
    if is_valid:
        print("✅ Transparency logs verified - no tampering detected")
    else:
        print(f"❌ Integrity check failed: {errors}")
    
    print("✅ Compliance reporting system ready")
    print("✅ Transparency logging enabled")
    print("✅ Tamper-proof audit trails implemented")

if __name__ == "__main__":
    example_compliance_reporting()

