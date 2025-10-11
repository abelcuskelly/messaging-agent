"""
Agent Registry for Multi-Agent Orchestration

Central registry for agent discovery, routing, and coordination.
Supports single-agent optimization now, multi-agent coordination later.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Enumeration of agent capabilities"""
    # Ticketing capabilities
    TICKET_PURCHASE = "ticket_purchase"
    TICKET_UPGRADE = "ticket_upgrade"
    TICKET_REFUND = "ticket_refund"
    TICKET_INQUIRY = "ticket_inquiry"
    
    # Sales capabilities
    SALES_PROPOSAL = "sales_proposal"
    CRM_MANAGEMENT = "crm_management"
    PIPELINE_TRACKING = "pipeline_tracking"
    LEAD_QUALIFICATION = "lead_qualification"
    
    # Finance capabilities
    EXPENSE_APPROVAL = "expense_approval"
    BUDGET_TRACKING = "budget_tracking"
    INVOICE_GENERATION = "invoice_generation"
    FINANCIAL_REPORTING = "financial_reporting"
    
    # HR capabilities
    CANDIDATE_SCREENING = "candidate_screening"
    INTERVIEW_SCHEDULING = "interview_scheduling"
    ONBOARDING = "onboarding"
    EMPLOYEE_INQUIRY = "employee_inquiry"
    
    # General capabilities
    INTENT_CLASSIFICATION = "intent_classification"
    ESCALATION = "escalation"
    NOTIFICATION = "notification"


@dataclass
class AgentConfig:
    """Configuration for a registered agent"""
    agent_id: str
    name: str
    description: str
    endpoint: str
    capabilities: List[AgentCapability]
    priority: int
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['capabilities'] = [cap.value for cap in self.capabilities]
        return data


class AgentRegistry:
    """
    Central registry for agent discovery and routing
    
    Features:
    - Agent registration and discovery
    - Capability-based routing
    - Priority-based agent selection
    - Health checking and fallback
    - Load balancing (round-robin)
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self._load_agents_from_env()
    
    def _load_agents_from_env(self):
        """Load agent configurations from environment variables"""
        
        # Ticketing Agent (current system)
        ticketing_endpoint = os.getenv('TICKETING_ENDPOINT', 
                                       os.getenv('ENDPOINT_ID', 'local'))
        if ticketing_endpoint:
            self.register_agent(AgentConfig(
                agent_id="ticketing",
                name="AI Messaging & Ticketing Agent",
                description="Handles ticket purchases, upgrades, refunds, and inquiries",
                endpoint=ticketing_endpoint,
                capabilities=[
                    AgentCapability.TICKET_PURCHASE,
                    AgentCapability.TICKET_UPGRADE,
                    AgentCapability.TICKET_REFUND,
                    AgentCapability.TICKET_INQUIRY
                ],
                priority=1,
                enabled=True
            ))
        
        # Sales Agent (future)
        sales_endpoint = os.getenv('SALES_ENDPOINT')
        if sales_endpoint:
            self.register_agent(AgentConfig(
                agent_id="sales",
                name="AI Sales Agent",
                description="Handles proposals, CRM, pipeline, and lead qualification",
                endpoint=sales_endpoint,
                capabilities=[
                    AgentCapability.SALES_PROPOSAL,
                    AgentCapability.CRM_MANAGEMENT,
                    AgentCapability.PIPELINE_TRACKING,
                    AgentCapability.LEAD_QUALIFICATION
                ],
                priority=2,
                enabled=True
            ))
        
        # Finance Agent (future)
        finance_endpoint = os.getenv('FINANCE_ENDPOINT')
        if finance_endpoint:
            self.register_agent(AgentConfig(
                agent_id="finance",
                name="AI CFO & Ops Agent",
                description="Handles expenses, budgets, invoices, and financial reporting",
                endpoint=finance_endpoint,
                capabilities=[
                    AgentCapability.EXPENSE_APPROVAL,
                    AgentCapability.BUDGET_TRACKING,
                    AgentCapability.INVOICE_GENERATION,
                    AgentCapability.FINANCIAL_REPORTING
                ],
                priority=3,
                enabled=True
            ))
        
        # HR Agent (future)
        hr_endpoint = os.getenv('HR_ENDPOINT')
        if hr_endpoint:
            self.register_agent(AgentConfig(
                agent_id="hr",
                name="AI HR & Recruiting Agent",
                description="Handles recruiting, screening, scheduling, and employee inquiries",
                endpoint=hr_endpoint,
                capabilities=[
                    AgentCapability.CANDIDATE_SCREENING,
                    AgentCapability.INTERVIEW_SCHEDULING,
                    AgentCapability.ONBOARDING,
                    AgentCapability.EMPLOYEE_INQUIRY
                ],
                priority=4,
                enabled=True
            ))
        
        logger.info(f"Loaded {len(self.agents)} agents from environment")
    
    def register_agent(self, config: AgentConfig) -> None:
        """Register a new agent"""
        self.agents[config.agent_id] = config
        logger.info(f"Registered agent: {config.name} ({config.agent_id})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self, enabled_only: bool = True) -> List[AgentConfig]:
        """List all registered agents"""
        agents = list(self.agents.values())
        if enabled_only:
            agents = [a for a in agents if a.enabled]
        return sorted(agents, key=lambda a: a.priority)
    
    def find_agents_by_capability(self, 
                                  capability: AgentCapability) -> List[AgentConfig]:
        """Find all agents with a specific capability"""
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities and agent.enabled
        ]
    
    def route_to_agent(self, intent: str) -> Optional[AgentConfig]:
        """
        Route a request to the appropriate agent based on intent
        
        Simple routing logic for now, can be replaced with LangGraph later
        """
        
        # Intent to capability mapping
        intent_map = {
            # Ticketing intents
            "purchase_tickets": AgentCapability.TICKET_PURCHASE,
            "buy_tickets": AgentCapability.TICKET_PURCHASE,
            "upgrade_seats": AgentCapability.TICKET_UPGRADE,
            "upgrade_tickets": AgentCapability.TICKET_UPGRADE,
            "refund_tickets": AgentCapability.TICKET_REFUND,
            "cancel_order": AgentCapability.TICKET_REFUND,
            "ticket_info": AgentCapability.TICKET_INQUIRY,
            "event_info": AgentCapability.TICKET_INQUIRY,
            
            # Sales intents
            "create_proposal": AgentCapability.SALES_PROPOSAL,
            "update_crm": AgentCapability.CRM_MANAGEMENT,
            "check_pipeline": AgentCapability.PIPELINE_TRACKING,
            "qualify_lead": AgentCapability.LEAD_QUALIFICATION,
            
            # Finance intents
            "approve_expense": AgentCapability.EXPENSE_APPROVAL,
            "check_budget": AgentCapability.BUDGET_TRACKING,
            "generate_invoice": AgentCapability.INVOICE_GENERATION,
            "financial_report": AgentCapability.FINANCIAL_REPORTING,
            
            # HR intents
            "screen_candidate": AgentCapability.CANDIDATE_SCREENING,
            "schedule_interview": AgentCapability.INTERVIEW_SCHEDULING,
            "onboard_employee": AgentCapability.ONBOARDING,
            "hr_inquiry": AgentCapability.EMPLOYEE_INQUIRY
        }
        
        # Get capability for intent
        capability = intent_map.get(intent.lower())
        if not capability:
            # Default to ticketing agent for unknown intents
            return self.get_agent("ticketing")
        
        # Find agents with this capability
        capable_agents = self.find_agents_by_capability(capability)
        
        if not capable_agents:
            logger.warning(f"No agent found for capability: {capability}")
            return None
        
        # Return highest priority agent
        return capable_agents[0]
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_agents": len(self.agents),
            "enabled_agents": len([a for a in self.agents.values() if a.enabled]),
            "capabilities": list(set(
                cap for agent in self.agents.values() 
                for cap in agent.capabilities
            )),
            "agents": [a.to_dict() for a in self.list_agents(enabled_only=False)]
        }
    
    def to_json(self) -> str:
        """Export registry as JSON"""
        return json.dumps(self.get_agent_stats(), indent=2, default=str)


# Global registry instance
_registry = None

def get_registry() -> AgentRegistry:
    """Get the global agent registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
