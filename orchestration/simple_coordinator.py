"""
Simple Multi-Agent Coordinator

Lightweight coordinator for multi-agent workflows without LangGraph.
Suitable for basic sequential and parallel agent coordination.
Can be upgraded to LangGraph when complex workflows are needed.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from google.cloud import aiplatform

from orchestration.agent_registry import AgentRegistry, get_registry, AgentConfig

logger = logging.getLogger(__name__)


class CoordinationStrategy(str, Enum):
    """Coordination strategies for multi-agent workflows"""
    SEQUENTIAL = "sequential"  # Execute agents one after another
    PARALLEL = "parallel"      # Execute agents in parallel
    CONDITIONAL = "conditional"  # Execute based on conditions
    DELEGATED = "delegated"    # One agent delegates to another


@dataclass
class AgentTask:
    """A task to be executed by an agent"""
    agent_id: str
    input_data: Dict[str, Any]
    depends_on: List[str] = None  # Task IDs this depends on
    condition: Optional[Callable] = None  # Condition to execute
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class AgentResult:
    """Result from an agent execution"""
    task_id: str
    agent_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0


class SimpleCoordinator:
    """
    Simple multi-agent coordinator without LangGraph
    
    Features:
    - Sequential execution
    - Parallel execution
    - Conditional routing
    - Result aggregation
    - Error handling and fallback
    - Execution history
    
    Suitable for:
    - Simple multi-step workflows
    - Agent delegation patterns
    - Basic orchestration needs
    
    Upgrade to LangGraph when you need:
    - Complex state machines
    - Cyclic workflows
    - Human-in-the-loop
    - Advanced branching logic
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or get_registry()
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute a single agent task"""
        start_time = time.time()
        
        try:
            # Get agent configuration
            agent_config = self.registry.get_agent(task.agent_id)
            if not agent_config:
                return AgentResult(
                    task_id=task.agent_id,
                    agent_id=task.agent_id,
                    success=False,
                    output=None,
                    error=f"Agent not found: {task.agent_id}"
                )
            
            # Check condition if present
            if task.condition and not task.condition():
                logger.info(f"Skipping task {task.agent_id}: condition not met")
                return AgentResult(
                    task_id=task.agent_id,
                    agent_id=task.agent_id,
                    success=True,
                    output={"skipped": True, "reason": "condition_not_met"},
                    execution_time_ms=0
                )
            
            # Execute agent
            logger.info(f"Executing agent: {agent_config.name}")
            output = await self._call_agent(agent_config, task.input_data)
            
            execution_time = (time.time() - start_time) * 1000
            
            return AgentResult(
                task_id=task.agent_id,
                agent_id=task.agent_id,
                success=True,
                output=output,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error executing agent {task.agent_id}: {e}")
            execution_time = (time.time() - start_time) * 1000
            
            return AgentResult(
                task_id=task.agent_id,
                agent_id=task.agent_id,
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    async def _call_agent(self, 
                         agent_config: AgentConfig, 
                         input_data: Dict[str, Any]) -> Any:
        """Call an agent endpoint"""
        # Initialize Vertex AI endpoint
        endpoint = aiplatform.Endpoint(agent_config.endpoint)
        
        # Prepare request
        instances = [{
            "messages": input_data.get("messages", []),
            "context": input_data.get("context", {})
        }]
        
        # Make prediction
        response = endpoint.predict(instances=instances)
        
        return response.predictions[0] if response.predictions else None
    
    async def execute_sequential(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """
        Execute tasks sequentially (one after another)
        
        Use when:
        - Output of one agent is needed by the next
        - Strict ordering is required
        - Error in one should stop the rest
        """
        results = []
        context = {}  # Shared context across tasks
        
        for task in tasks:
            # Add context from previous results
            task.input_data["context"] = context
            
            # Execute task
            result = await self.execute_task(task)
            results.append(result)
            
            # Stop on error
            if not result.success:
                logger.error(f"Sequential execution stopped at {task.agent_id}")
                break
            
            # Update context
            context[task.agent_id] = result.output
        
        self._log_execution("sequential", tasks, results)
        return results
    
    async def execute_parallel(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """
        Execute tasks in parallel (all at once)
        
        Use when:
        - Tasks are independent
        - Speed is important
        - Errors in one shouldn't block others
        """
        # Execute all tasks concurrently
        task_coroutines = [self.execute_task(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentResult(
                    task_id=tasks[i].agent_id,
                    agent_id=tasks[i].agent_id,
                    success=False,
                    output=None,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        self._log_execution("parallel", tasks, processed_results)
        return processed_results
    
    async def execute_conditional(self, 
                                  tasks: List[AgentTask],
                                  router: Callable[[Dict], str]) -> AgentResult:
        """
        Execute task based on routing condition
        
        Use when:
        - Need to choose one agent based on input
        - Intent-based routing
        - Dynamic agent selection
        """
        # Route to appropriate task
        task_map = {task.agent_id: task for task in tasks}
        selected_agent_id = router(tasks[0].input_data if tasks else {})
        
        selected_task = task_map.get(selected_agent_id)
        if not selected_task:
            logger.error(f"No task found for routed agent: {selected_agent_id}")
            return AgentResult(
                task_id="router",
                agent_id="router",
                success=False,
                output=None,
                error=f"No task found for agent: {selected_agent_id}"
            )
        
        # Execute selected task
        result = await self.execute_task(selected_task)
        self._log_execution("conditional", [selected_task], [result])
        return result
    
    async def execute_workflow(self, 
                              tasks: List[AgentTask],
                              strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL) -> List[AgentResult]:
        """
        Execute a workflow of tasks with specified strategy
        """
        logger.info(f"Executing workflow with {len(tasks)} tasks using {strategy}")
        
        if strategy == CoordinationStrategy.SEQUENTIAL:
            return await self.execute_sequential(tasks)
        elif strategy == CoordinationStrategy.PARALLEL:
            return await self.execute_parallel(tasks)
        else:
            raise ValueError(f"Unsupported strategy for workflow: {strategy}")
    
    def _log_execution(self, 
                      strategy: str, 
                      tasks: List[AgentTask], 
                      results: List[AgentResult]) -> None:
        """Log execution for history and debugging"""
        execution_record = {
            "timestamp": time.time(),
            "strategy": strategy,
            "tasks": [task.agent_id for task in tasks],
            "results": [
                {
                    "agent_id": r.agent_id,
                    "success": r.success,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in results
            ],
            "total_time_ms": sum(r.execution_time_ms for r in results)
        }
        self.execution_history.append(execution_record)
        logger.info(f"Execution logged: {strategy} - {len(tasks)} tasks")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        total_executions = len(self.execution_history)
        total_time = sum(e["total_time_ms"] for e in self.execution_history)
        avg_time = total_time / total_executions if total_executions > 0 else 0
        
        strategies_used = {}
        for execution in self.execution_history:
            strategy = execution["strategy"]
            strategies_used[strategy] = strategies_used.get(strategy, 0) + 1
        
        return {
            "total_executions": total_executions,
            "total_time_ms": total_time,
            "avg_time_ms": avg_time,
            "strategies_used": strategies_used,
            "recent_executions": self.execution_history[-10:]  # Last 10
        }


# Example usage patterns

async def example_sequential_workflow():
    """
    Example: Sequential workflow for ticket purchase with expense approval
    """
    coordinator = SimpleCoordinator()
    
    tasks = [
        AgentTask(
            agent_id="ticketing",
            input_data={
                "messages": [{"role": "user", "content": "Book 10 tickets for tonight"}]
            }
        ),
        AgentTask(
            agent_id="finance",
            input_data={
                "messages": [{"role": "user", "content": "Approve expense for tickets"}]
            },
            depends_on=["ticketing"]
        )
    ]
    
    results = await coordinator.execute_sequential(tasks)
    return results


async def example_parallel_workflow():
    """
    Example: Parallel workflow for notification to multiple channels
    """
    coordinator = SimpleCoordinator()
    
    tasks = [
        AgentTask(
            agent_id="ticketing",
            input_data={
                "messages": [{"role": "system", "content": "Send SMS confirmation"}]
            }
        ),
        AgentTask(
            agent_id="sales",
            input_data={
                "messages": [{"role": "system", "content": "Update CRM with purchase"}]
            }
        ),
        AgentTask(
            agent_id="finance",
            input_data={
                "messages": [{"role": "system", "content": "Log expense"}]
            }
        )
    ]
    
    results = await coordinator.execute_parallel(tasks)
    return results


async def example_conditional_routing():
    """
    Example: Route to appropriate agent based on intent
    """
    coordinator = SimpleCoordinator()
    
    def router(input_data: Dict) -> str:
        """Route based on message content"""
        message = input_data["messages"][0]["content"].lower()
        if "ticket" in message or "seat" in message:
            return "ticketing"
        elif "proposal" in message or "crm" in message:
            return "sales"
        elif "expense" in message or "budget" in message:
            return "finance"
        else:
            return "ticketing"  # Default
    
    tasks = [
        AgentTask(agent_id="ticketing", input_data={"messages": []}),
        AgentTask(agent_id="sales", input_data={"messages": []}),
        AgentTask(agent_id="finance", input_data={"messages": []})
    ]
    
    # Set actual input
    tasks[0].input_data = {
        "messages": [{"role": "user", "content": "I need tickets"}]
    }
    
    result = await coordinator.execute_conditional(tasks, router)
    return result
