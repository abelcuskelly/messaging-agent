"""
Orchestration Layer for Multi-Agent Systems

This package provides orchestration capabilities for single and multi-agent systems.

Components:
- agent_registry: Central registry for agent discovery and routing
- simple_coordinator: Lightweight multi-agent coordinator (no LangGraph)
- langgraph_placeholder: Placeholder for complex LangGraph workflows
- optimizations: Performance optimizations for single-agent systems

Usage:
    # Single agent (current system)
    from orchestration.optimizations import get_optimizer
    optimizer = get_optimizer()
    
    # Multi-agent coordination
    from orchestration.simple_coordinator import SimpleCoordinator
    coordinator = SimpleCoordinator()
    
    # Agent registry
    from orchestration.agent_registry import get_registry
    registry = get_registry()
"""

from orchestration.agent_registry import (
    AgentRegistry,
    AgentConfig,
    AgentCapability,
    get_registry
)

from orchestration.simple_coordinator import (
    SimpleCoordinator,
    AgentTask,
    AgentResult,
    CoordinationStrategy
)

from orchestration.optimizations import (
    SingleAgentOptimizer,
    PromptOptimizer,
    PerformanceMetrics,
    get_optimizer
)

__all__ = [
    # Agent Registry
    "AgentRegistry",
    "AgentConfig", 
    "AgentCapability",
    "get_registry",
    
    # Simple Coordinator
    "SimpleCoordinator",
    "AgentTask",
    "AgentResult",
    "CoordinationStrategy",
    
    # Optimizations
    "SingleAgentOptimizer",
    "PromptOptimizer",
    "PerformanceMetrics",
    "get_optimizer"
]

__version__ = "0.1.0"
