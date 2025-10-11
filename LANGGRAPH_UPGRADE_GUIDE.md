# LangGraph Upgrade Guide

A step-by-step guide for upgrading from Simple Coordinator to LangGraph when your workflows become complex.

## 📊 When to Upgrade

### Upgrade Triggers (ANY of these):
- ✅ You have **4+ agents** that need coordination
- ✅ Agents need to **call each other** (cyclic workflows)
- ✅ **Human approval** required in the workflow
- ✅ **Complex branching** logic (if-then-else trees)
- ✅ **Persistent state** needed across long-running workflows
- ✅ **Retry logic** with state recovery
- ✅ **Event-driven** workflows

### Stay with Simple Coordinator if:
- ❌ Only 2-3 agents
- ❌ Simple sequential or parallel flows
- ❌ No human intervention needed
- ❌ Stateless workflows

## 🚀 Upgrade Process

### Step 1: Install Dependencies

```bash
# Install LangGraph and LangChain
pip install langgraph==0.2.0 \
            langchain-google-vertexai==1.0.0 \
            langchain==0.1.0

# Or add to requirements.txt
echo "langgraph==0.2.0" >> requirements.txt
echo "langchain-google-vertexai==1.0.0" >> requirements.txt
echo "langchain==0.1.0" >> requirements.txt
```

### Step 2: Activate the LangGraph Code

The code is already written but commented out. Simply uncomment it:

```bash
# Option 1: Manual edit
# Open orchestration/langgraph_placeholder.py and remove all # comments

# Option 2: Use this script
python -c "
with open('orchestration/langgraph_placeholder.py', 'r') as f:
    lines = f.readlines()

# Remove comment markers from actual code (keep docstring comments)
activated = []
for line in lines:
    if line.strip().startswith('# ') and not line.strip().startswith('# '):
        activated.append(line[2:])  # Remove '# '
    else:
        activated.append(line)

with open('orchestration/langgraph_orchestrator.py', 'w') as f:
    f.writelines(activated)

print('✅ LangGraph code activated in langgraph_orchestrator.py')
"
```

### Step 3: Update Imports

Change your imports from placeholder to the active module:

```python
# Before (placeholder)
from orchestration.simple_coordinator import SimpleCoordinator

# After (with LangGraph)
from orchestration.langgraph_orchestrator import EnterpriseOrchestrator
```

### Step 4: Implement Your Workflow

Here's a complete example of a complex workflow that needs LangGraph:

```python
from orchestration.langgraph_orchestrator import EnterpriseOrchestrator
from langgraph.graph import StateGraph, END

class ComplexTicketWorkflow:
    """
    Example: Purchase tickets with multi-level approval and notifications
    """
    
    def __init__(self, project_id: str, region: str):
        self.orchestrator = EnterpriseOrchestrator(project_id, region)
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the complex workflow graph"""
        graph = StateGraph(WorkflowState)
        
        # Add nodes for each step
        graph.add_node("check_inventory", self.check_ticket_inventory)
        graph.add_node("calculate_price", self.calculate_total_price)
        graph.add_node("check_budget", self.check_customer_budget)
        graph.add_node("manager_approval", self.get_manager_approval)
        graph.add_node("director_approval", self.get_director_approval)
        graph.add_node("process_payment", self.process_payment)
        graph.add_node("send_tickets", self.send_tickets)
        graph.add_node("update_crm", self.update_crm)
        graph.add_node("send_notifications", self.send_notifications)
        graph.add_node("handle_error", self.handle_error)
        
        # Define the flow
        graph.set_entry_point("check_inventory")
        
        # Conditional edges based on inventory
        graph.add_conditional_edges(
            "check_inventory",
            self.has_inventory,
            {
                "available": "calculate_price",
                "sold_out": "handle_error"
            }
        )
        
        # After price calculation, check budget
        graph.add_edge("calculate_price", "check_budget")
        
        # Conditional approval based on amount
        graph.add_conditional_edges(
            "check_budget",
            self.determine_approval_level,
            {
                "auto_approve": "process_payment",
                "manager_approval": "manager_approval",
                "director_approval": "director_approval",
                "reject": "handle_error"
            }
        )
        
        # Manager approval flow
        graph.add_conditional_edges(
            "manager_approval",
            self.check_approval,
            {
                "approved": "process_payment",
                "escalate": "director_approval",
                "rejected": "handle_error"
            }
        )
        
        # Director approval flow
        graph.add_conditional_edges(
            "director_approval",
            self.check_approval,
            {
                "approved": "process_payment",
                "rejected": "handle_error"
            }
        )
        
        # After payment, parallel execution
        graph.add_edge("process_payment", "send_tickets")
        graph.add_edge("process_payment", "update_crm")
        graph.add_edge("process_payment", "send_notifications")
        
        # All success paths lead to END
        graph.add_edge("send_tickets", END)
        graph.add_edge("update_crm", END)
        graph.add_edge("send_notifications", END)
        graph.add_edge("handle_error", END)
        
        return graph.compile()
    
    async def run(self, request: Dict) -> Dict:
        """Execute the workflow"""
        initial_state = {
            "messages": [{"role": "user", "content": request["message"]}],
            "ticket_quantity": request.get("quantity", 1),
            "user_id": request.get("user_id"),
            "intent": "purchase_tickets",
            "requires_approval": False,
            "approved": False,
            "results": {}
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
```

### Step 5: Migration Strategy

#### Option A: Gradual Migration (Recommended)

Keep both coordinators and use based on complexity:

```python
from orchestration import SimpleCoordinator
from orchestration.langgraph_orchestrator import EnterpriseOrchestrator

class HybridOrchestrator:
    """Use simple or complex based on workflow needs"""
    
    def __init__(self):
        self.simple = SimpleCoordinator()
        self.complex = EnterpriseOrchestrator(project_id, region)
    
    async def execute(self, workflow_type: str, tasks: List[AgentTask]):
        if workflow_type in ["sequential", "parallel"]:
            # Use simple coordinator for basic flows
            return await self.simple.execute_workflow(tasks)
        else:
            # Use LangGraph for complex flows
            return await self.complex.execute(tasks)
```

#### Option B: Full Migration

Replace all SimpleCoordinator usage with LangGraph:

```python
# Before
coordinator = SimpleCoordinator()
results = await coordinator.execute_sequential(tasks)

# After
orchestrator = EnterpriseOrchestrator(project_id, region)
results = await orchestrator.execute(messages)
```

### Step 6: Test the Upgrade

Create test cases for your complex workflows:

```python
import pytest
from orchestration.langgraph_orchestrator import EnterpriseOrchestrator

@pytest.mark.asyncio
async def test_complex_approval_workflow():
    orchestrator = EnterpriseOrchestrator("test-project", "us-central1")
    
    # Test high-value purchase requiring approval
    result = await orchestrator.execute([
        {"role": "user", "content": "Buy 500 tickets for $50,000"}
    ])
    
    assert result["requires_approval"] == True
    assert "director_approval" in result["results"]

@pytest.mark.asyncio
async def test_parallel_notification():
    orchestrator = EnterpriseOrchestrator("test-project", "us-central1")
    
    # Test parallel execution after purchase
    result = await orchestrator.execute([
        {"role": "user", "content": "Purchase confirmed"}
    ])
    
    assert "send_tickets" in result["results"]
    assert "update_crm" in result["results"]
    assert "send_notifications" in result["results"]
```

## 🔄 Key Differences After Upgrade

### Simple Coordinator
```python
# Linear, predictable flow
tasks = [task1, task2, task3]
results = await coordinator.execute_sequential(tasks)
```

### LangGraph
```python
# Complex, stateful graph
graph = StateGraph()
graph.add_conditional_edges(...)  # Dynamic routing
graph.add_edge(...)               # Parallel execution
result = await graph.ainvoke(state)
```

## 📊 Performance Impact

| Metric | Simple Coordinator | LangGraph | Difference |
|--------|-------------------|-----------|------------|
| Setup Time | <1ms | 50-100ms | +50-100ms |
| Execution Overhead | ~10ms | 100-300ms | +90-290ms |
| Memory Usage | ~10MB | ~50MB | +40MB |
| Dependencies | 0 | 3+ packages | More complex |

## 🎯 LangGraph Advantages

### 1. State Persistence
```python
# LangGraph maintains state across steps
state = {
    "conversation": [...],
    "approvals": {...},
    "context": {...}
}
# State automatically flows through the graph
```

### 2. Complex Conditionals
```python
# Multiple branching paths
graph.add_conditional_edges(
    "node",
    condition_function,
    {
        "path1": "node1",
        "path2": "node2",
        "path3": "node3",
        "default": "error_handler"
    }
)
```

### 3. Human-in-the-Loop
```python
# Wait for human approval
graph.add_node("human_approval", wait_for_human_input)
graph.add_edge("requires_approval", "human_approval")
graph.add_edge("human_approval", "continue_or_stop")
```

### 4. Error Recovery
```python
# Sophisticated error handling
graph.add_node("retry_with_backoff", retry_handler)
graph.add_node("save_checkpoint", checkpoint_saver)
graph.add_node("restore_from_checkpoint", checkpoint_restorer)
```

## 🚨 Common Pitfalls

### 1. Over-Engineering
❌ **Don't** use LangGraph for simple flows:
```python
# Overkill for simple sequential flow
graph = StateGraph()  # Too complex!
graph.add_edge("A", "B")
graph.add_edge("B", "C")
```

✅ **Do** use Simple Coordinator:
```python
# Perfect for simple flows
await coordinator.execute_sequential([A, B, C])
```

### 2. State Management
❌ **Don't** forget to initialize state:
```python
# Missing required state fields
await graph.ainvoke({})  # Will fail!
```

✅ **Do** provide complete initial state:
```python
await graph.ainvoke({
    "messages": [],
    "intent": "",
    "results": {},
    "error": None
})
```

### 3. Debugging
LangGraph workflows are harder to debug. Use verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug nodes
graph.add_node("debug_state", lambda state: print(f"State: {state}"))
```

## 📝 Rollback Plan

If LangGraph causes issues, you can quickly rollback:

```bash
# 1. Re-comment the code
mv orchestration/langgraph_orchestrator.py orchestration/langgraph_orchestrator.py.backup
cp orchestration/langgraph_placeholder.py orchestration/langgraph_orchestrator.py

# 2. Switch back to Simple Coordinator
# Update imports back to SimpleCoordinator

# 3. Uninstall LangGraph (optional)
pip uninstall langgraph langchain-google-vertexai
```

## ✅ Upgrade Checklist

- [ ] Workflow requires 4+ agents
- [ ] Complex branching logic needed
- [ ] Human approval required
- [ ] Install LangGraph dependencies
- [ ] Uncomment langgraph_placeholder.py
- [ ] Implement workflow as StateGraph
- [ ] Test complex scenarios
- [ ] Monitor performance impact
- [ ] Document the workflow
- [ ] Train team on LangGraph

## 🎯 Summary

**Upgrade to LangGraph when:**
- Simple Coordinator can't handle your complexity
- You need stateful, persistent workflows
- Human approval is required
- Workflows have many conditional branches

**Stay with Simple Coordinator when:**
- 2-3 agents are sufficient
- Workflows are linear or simply parallel
- Low latency is critical
- Simplicity is valued

The upgrade path is smooth because the code is already written - you just need to uncomment and adapt it to your specific complex workflows!
