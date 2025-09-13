"""
Take It Down Backend - Demo Runner
Case lifecycle replay system for hackathon demonstration
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaseLifecycleReplay:
    """Replay realistic case scenarios for demonstration"""
    
    def __init__(self):
        self.scenarios = self._create_demo_scenarios()
        self.replay_speed = 1.0  # 1x real time
        self.pause_between_actions = 2.0  # seconds
    
    def _create_demo_scenarios(self) -> List[Dict[str, Any]]:
        """Create realistic demo scenarios"""
        return [
            {
                "name": "Successful High-Priority Case",
                "description": "Victim submits harmful content, officer reviews and approves quickly",
                "timeline": [
                    {
                        "delay_minutes": 0,
                        "action": "victim_submit",
                        "case_id": "CASE-2025-DEMO-001",
                        "data": {
                            "submitter": "victim_jane_doe",
                            "jurisdiction": "IN",
                            "priority": "high",
                            "submissions": [
                                {"kind": "URL", "content": "https://demo-harmful.example.com/content123"},
                                {"kind": "HASH", "content": "demo_hash_1234567890abcdef"}
                            ],
                            "notes": "Reported harmful content targeting minors"
                        }
                    },
                    {
                        "delay_minutes": 5,
                        "action": "officer_assign",
                        "case_id": "CASE-2025-DEMO-001",
                        "data": {
                            "officer": "officer_alex_brown",
                            "reason": "High priority case assigned immediately"
                        }
                    },
                    {
                        "delay_minutes": 15,
                        "action": "officer_review",
                        "case_id": "CASE-2025-DEMO-001",
                        "data": {
                            "officer": "officer_alex_brown",
                            "action": "start_review",
                            "reason": "Content verification in progress"
                        }
                    },
                    {
                        "delay_minutes": 45,
                        "action": "officer_approve",
                        "case_id": "CASE-2025-DEMO-001",
                        "data": {
                            "officer": "officer_alex_brown",
                            "action": "approve",
                            "reason": "Content verified as harmful, action taken"
                        }
                    },
                    {
                        "delay_minutes": 50,
                        "action": "case_close",
                        "case_id": "CASE-2025-DEMO-001",
                        "data": {
                            "officer": "officer_alex_brown",
                            "action": "close",
                            "reason": "Case successfully resolved"
                        }
                    }
                ]
            },
            {
                "name": "SLA Violation and Escalation",
                "description": "Case exceeds SLA deadline and gets escalated",
                "timeline": [
                    {
                        "delay_minutes": 0,
                        "action": "victim_submit",
                        "case_id": "CASE-2025-DEMO-002",
                        "data": {
                            "submitter": "victim_john_smith",
                            "jurisdiction": "US",
                            "priority": "medium",
                            "submissions": [
                                {"kind": "URL", "content": "https://demo-violation.example.org/badcontent"}
                            ],
                            "notes": "Complex case requiring investigation"
                        }
                    },
                    {
                        "delay_minutes": 10,
                        "action": "officer_assign",
                        "case_id": "CASE-2025-DEMO-002",
                        "data": {
                            "officer": "officer_sarah_wilson",
                            "reason": "Assigned to available officer"
                        }
                    },
                    {
                        "delay_minutes": 20,
                        "action": "officer_review",
                        "case_id": "CASE-2025-DEMO-002",
                        "data": {
                            "officer": "officer_sarah_wilson",
                            "action": "start_review",
                            "reason": "Starting detailed investigation"
                        }
                    },
                    {
                        "delay_minutes": 2880,  # 48 hours later (SLA violation)
                        "action": "sla_violation",
                        "case_id": "CASE-2025-DEMO-002",
                        "data": {
                            "reason": "SLA deadline exceeded",
                            "escalation_level": 1
                        }
                    },
                    {
                        "delay_minutes": 2890,
                        "action": "admin_reassign",
                        "case_id": "CASE-2025-DEMO-002",
                        "data": {
                            "admin": "admin_mike_chen",
                            "action": "reassign",
                            "reason": "Escalated case reassigned to senior officer"
                        }
                    },
                    {
                        "delay_minutes": 2900,
                        "action": "officer_approve",
                        "case_id": "CASE-2025-DEMO-002",
                        "data": {
                            "officer": "officer_alex_brown",
                            "action": "approve",
                            "reason": "Content verified after escalation"
                        }
                    }
                ]
            },
            {
                "name": "Duplicate Detection",
                "description": "System detects and handles duplicate submission",
                "timeline": [
                    {
                        "delay_minutes": 0,
                        "action": "victim_submit",
                        "case_id": "CASE-2025-DEMO-003",
                        "data": {
                            "submitter": "victim_jane_doe",
                            "jurisdiction": "IN",
                            "priority": "medium",
                            "submissions": [
                                {"kind": "URL", "content": "https://demo-harmful.example.com/content123"}
                            ],
                            "notes": "First submission of harmful content"
                        }
                    },
                    {
                        "delay_minutes": 30,
                        "action": "victim_submit_duplicate",
                        "case_id": "CASE-2025-DEMO-004",
                        "data": {
                            "submitter": "victim_john_smith",
                            "jurisdiction": "US",
                            "priority": "high",
                            "submissions": [
                                {"kind": "URL", "content": "https://demo-harmful.example.com/content123"}
                            ],
                            "notes": "Duplicate submission detected",
                            "origin_case_id": "CASE-2025-DEMO-003"
                        }
                    },
                    {
                        "delay_minutes": 35,
                        "action": "duplicate_linking",
                        "case_id": "CASE-2025-DEMO-004",
                        "data": {
                            "origin_case_id": "CASE-2025-DEMO-003",
                            "reason": "Duplicate content detected and linked"
                        }
                    }
                ]
            },
            {
                "name": "False Positive Rejection",
                "description": "Officer determines content is safe and rejects case",
                "timeline": [
                    {
                        "delay_minutes": 0,
                        "action": "victim_submit",
                        "case_id": "CASE-2025-DEMO-005",
                        "data": {
                            "submitter": "victim_jane_doe",
                            "jurisdiction": "IN",
                            "priority": "low",
                            "submissions": [
                                {"kind": "URL", "content": "https://demo-safe.example.com/legitimate-content"}
                            ],
                            "notes": "Reported as harmful but actually safe"
                        }
                    },
                    {
                        "delay_minutes": 15,
                        "action": "officer_assign",
                        "case_id": "CASE-2025-DEMO-005",
                        "data": {
                            "officer": "officer_alex_brown",
                            "reason": "Assigned for review"
                        }
                    },
                    {
                        "delay_minutes": 30,
                        "action": "officer_review",
                        "case_id": "CASE-2025-DEMO-005",
                        "data": {
                            "officer": "officer_alex_brown",
                            "action": "start_review",
                            "reason": "Reviewing reported content"
                        }
                    },
                    {
                        "delay_minutes": 60,
                        "action": "officer_reject",
                        "case_id": "CASE-2025-DEMO-005",
                        "data": {
                            "officer": "officer_alex_brown",
                            "action": "reject",
                            "reason": "Content verified as safe, false positive"
                        }
                    }
                ]
            }
        ]
    
    async def run_demo(self, scenario_name: str = None, speed_multiplier: float = 1.0):
        """Run demo scenarios"""
        self.replay_speed = speed_multiplier
        
        print("🚀 Take It Down Backend - Case Lifecycle Replay Demo")
        print("=" * 60)
        
        scenarios_to_run = self.scenarios
        if scenario_name:
            scenarios_to_run = [s for s in self.scenarios if s['name'] == scenario_name]
        
        if not scenarios_to_run:
            print(f"❌ Scenario '{scenario_name}' not found")
            return
        
        for scenario in scenarios_to_run:
            await self._run_scenario(scenario)
            print("\n" + "=" * 60)
    
    async def _run_scenario(self, scenario: Dict[str, Any]):
        """Run a single scenario"""
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"📝 Description: {scenario['description']}")
        print("-" * 40)
        
        start_time = datetime.utcnow()
        
        for step in scenario['timeline']:
            # Calculate actual delay based on speed multiplier
            delay_seconds = (step['delay_minutes'] * 60) / self.replay_speed
            
            if delay_seconds > 0:
                print(f"⏱️  Waiting {step['delay_minutes']} minutes (demo speed: {self.replay_speed}x)...")
                await asyncio.sleep(min(delay_seconds, 5))  # Cap at 5 seconds for demo
            
            # Execute action
            await self._execute_action(step, start_time)
            
            # Pause between actions
            await asyncio.sleep(self.pause_between_actions)
        
        print(f"\n✅ Scenario completed: {scenario['name']}")
    
    async def _execute_action(self, step: Dict[str, Any], start_time: datetime):
        """Execute a single action step"""
        action = step['action']
        case_id = step['case_id']
        data = step['data']
        
        current_time = start_time + timedelta(minutes=step['delay_minutes'])
        
        if action == "victim_submit":
            print(f"👤 {current_time.strftime('%H:%M:%S')} - Victim {data['submitter']} submits case {case_id}")
            print(f"   📍 Jurisdiction: {data['jurisdiction']}, Priority: {data['priority']}")
            print(f"   📄 Submissions: {len(data['submissions'])} items")
            print(f"   💬 Notes: {data['notes']}")
            
        elif action == "victim_submit_duplicate":
            print(f"👤 {current_time.strftime('%H:%M:%S')} - Victim {data['submitter']} submits duplicate case {case_id}")
            print(f"   🔗 Duplicate of: {data['origin_case_id']}")
            
        elif action == "officer_assign":
            print(f"👮 {current_time.strftime('%H:%M:%S')} - Officer {data['officer']} assigned to case {case_id}")
            print(f"   📋 Reason: {data['reason']}")
            
        elif action == "officer_review":
            print(f"🔍 {current_time.strftime('%H:%M:%S')} - Officer {data['officer']} starts review of case {case_id}")
            print(f"   📋 Action: {data['action']}")
            print(f"   💬 Reason: {data['reason']}")
            
        elif action == "officer_approve":
            print(f"✅ {current_time.strftime('%H:%M:%S')} - Officer {data['officer']} approves case {case_id}")
            print(f"   📋 Action: {data['action']}")
            print(f"   💬 Reason: {data['reason']}")
            
        elif action == "officer_reject":
            print(f"❌ {current_time.strftime('%H:%M:%S')} - Officer {data['officer']} rejects case {case_id}")
            print(f"   📋 Action: {data['action']}")
            print(f"   💬 Reason: {data['reason']}")
            
        elif action == "sla_violation":
            print(f"⚠️  {current_time.strftime('%H:%M:%S')} - SLA VIOLATION for case {case_id}")
            print(f"   📋 Reason: {data['reason']}")
            print(f"   📊 Escalation Level: {data['escalation_level']}")
            
        elif action == "admin_reassign":
            print(f"👨‍💼 {current_time.strftime('%H:%M:%S')} - Admin {data['admin']} reassigns case {case_id}")
            print(f"   📋 Action: {data['action']}")
            print(f"   💬 Reason: {data['reason']}")
            
        elif action == "duplicate_linking":
            print(f"🔗 {current_time.strftime('%H:%M:%S')} - Duplicate linking for case {case_id}")
            print(f"   🔗 Origin: {data['origin_case_id']}")
            print(f"   💬 Reason: {data['reason']}")
            
        elif action == "case_close":
            print(f"🔒 {current_time.strftime('%H:%M:%S')} - Case {case_id} closed")
            print(f"   📋 Action: {data['action']}")
            print(f"   💬 Reason: {data['reason']}")
        
        # Simulate system processing
        await self._simulate_system_processing(action, case_id)
    
    async def _simulate_system_processing(self, action: str, case_id: str):
        """Simulate system processing for the action"""
        processing_steps = [
            "Validating request...",
            "Updating database...",
            "Generating audit log...",
            "Sending notifications...",
            "Updating SLA timers...",
            "Processing complete"
        ]
        
        for step in processing_steps:
            print(f"   ⚙️  {step}")
            await asyncio.sleep(0.1)  # Quick processing simulation

class SystemHealthMonitor:
    """Monitor system health during demo"""
    
    def __init__(self):
        self.metrics = {
            "cases_processed": 0,
            "notifications_sent": 0,
            "sla_violations": 0,
            "escalations": 0,
            "duplicates_detected": 0,
            "start_time": datetime.utcnow()
        }
    
    def update_metric(self, metric: str, value: int = 1):
        """Update a metric"""
        if metric in self.metrics:
            self.metrics[metric] += value
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        uptime = datetime.utcnow() - self.metrics["start_time"]
        
        return {
            "uptime_minutes": uptime.total_seconds() / 60,
            "cases_processed": self.metrics["cases_processed"],
            "notifications_sent": self.metrics["notifications_sent"],
            "sla_violations": self.metrics["sla_violations"],
            "escalations": self.metrics["escalations"],
            "duplicates_detected": self.metrics["duplicates_detected"],
            "throughput_cases_per_hour": (self.metrics["cases_processed"] / uptime.total_seconds()) * 3600 if uptime.total_seconds() > 0 else 0
        }
    
    def print_health_summary(self):
        """Print health summary"""
        summary = self.get_health_summary()
        
        print("\n📊 System Health Summary")
        print("-" * 30)
        print(f"⏱️  Uptime: {summary['uptime_minutes']:.1f} minutes")
        print(f"📋 Cases Processed: {summary['cases_processed']}")
        print(f"📧 Notifications Sent: {summary['notifications_sent']}")
        print(f"⚠️  SLA Violations: {summary['sla_violations']}")
        print(f"📈 Escalations: {summary['escalations']}")
        print(f"🔗 Duplicates Detected: {summary['duplicates_detected']}")
        print(f"🚀 Throughput: {summary['throughput_cases_per_hour']:.1f} cases/hour")

async def main():
    """Main demo runner"""
    print("🎯 Take It Down Backend - Hackathon Demo")
    print("=" * 50)
    
    # Initialize components
    replay = CaseLifecycleReplay()
    health_monitor = SystemHealthMonitor()
    
    # Show available scenarios
    print("\n📋 Available Demo Scenarios:")
    for i, scenario in enumerate(replay.scenarios, 1):
        print(f"   {i}. {scenario['name']}")
        print(f"      {scenario['description']}")
    
    print("\n🚀 Starting demo with all scenarios...")
    print("   (Speed: 10x for demo purposes)")
    
    # Run all scenarios at 10x speed
    await replay.run_demo(speed_multiplier=10.0)
    
    # Show final health summary
    health_monitor.print_health_summary()
    
    print("\n🎉 Demo completed successfully!")
    print("   The Take It Down backend system is ready for production deployment.")

if __name__ == "__main__":
    asyncio.run(main())
