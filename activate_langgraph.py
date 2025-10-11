#!/usr/bin/env python3
"""
LangGraph Activation Script

This script helps you upgrade from Simple Coordinator to LangGraph
when your workflows become complex enough to need it.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple

def check_complexity_needs() -> Tuple[bool, str]:
    """Interactive questionnaire to determine if you need LangGraph"""
    print("\n🤔 Let's determine if you need LangGraph...")
    print("=" * 50)
    
    score = 0
    reasons = []
    
    # Question 1: Number of agents
    agents = input("\n1. How many agents need coordination? (enter number): ")
    try:
        num_agents = int(agents)
        if num_agents >= 4:
            score += 3
            reasons.append(f"✓ {num_agents} agents (LangGraph recommended for 4+)")
        elif num_agents == 3:
            score += 1
            reasons.append(f"~ {num_agents} agents (borderline)")
        else:
            reasons.append(f"✗ {num_agents} agents (Simple Coordinator is fine)")
    except:
        reasons.append("✗ Invalid agent count")
    
    # Question 2: Workflow complexity
    print("\n2. Do you need any of these? (y/n for each)")
    
    if input("   - Agents calling each other (cycles)? ").lower() == 'y':
        score += 3
        reasons.append("✓ Cyclic workflows needed")
    
    if input("   - Human approval in workflow? ").lower() == 'y':
        score += 3
        reasons.append("✓ Human-in-the-loop required")
    
    if input("   - Complex if-then-else branching? ").lower() == 'y':
        score += 2
        reasons.append("✓ Complex branching logic")
    
    if input("   - Workflow state persistence? ").lower() == 'y':
        score += 2
        reasons.append("✓ Persistent state needed")
    
    if input("   - Retry with state recovery? ").lower() == 'y':
        score += 2
        reasons.append("✓ State recovery required")
    
    # Recommendation
    print("\n" + "=" * 50)
    print("📊 Analysis Results:")
    for reason in reasons:
        print(f"  {reason}")
    
    print(f"\n🎯 Score: {score}/15")
    
    if score >= 6:
        print("✅ Recommendation: UPGRADE TO LANGGRAPH")
        return True, "Your workflow complexity justifies LangGraph"
    elif score >= 3:
        print("🤔 Recommendation: CONSIDER LANGGRAPH")
        return False, "You might benefit from LangGraph, but Simple Coordinator could work"
    else:
        print("❌ Recommendation: KEEP SIMPLE COORDINATOR")
        return False, "Simple Coordinator is sufficient for your needs"

def install_dependencies():
    """Install LangGraph and dependencies"""
    print("\n📦 Installing LangGraph dependencies...")
    
    packages = [
        "langgraph==0.2.0",
        "langchain==0.1.0",
        "langchain-google-vertexai==1.0.0"
    ]
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install"] + packages,
            check=True
        )
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def activate_langgraph_code():
    """Uncomment the LangGraph code"""
    print("\n🔧 Activating LangGraph code...")
    
    placeholder_file = Path("orchestration/langgraph_placeholder.py")
    output_file = Path("orchestration/langgraph_orchestrator.py")
    
    if not placeholder_file.exists():
        print("❌ langgraph_placeholder.py not found!")
        return False
    
    with open(placeholder_file, 'r') as f:
        lines = f.readlines()
    
    # Uncomment the code (but keep docstrings and real comments)
    activated = []
    in_docstring = False
    
    for line in lines:
        # Track docstrings
        if '"""' in line:
            in_docstring = not in_docstring
        
        # Uncomment code lines (but not docstrings or section comments)
        if line.startswith('# ') and not in_docstring:
            # Check if it's a code line (has common Python keywords/symbols)
            uncommented = line[2:]
            if any(keyword in uncommented for keyword in 
                   ['import ', 'from ', 'class ', 'def ', 'async ', 
                    'return ', 'if ', 'else:', 'for ', 'while ', 
                    '=', '(', ')', '{', '}', '[', ']', '@']):
                activated.append(uncommented)
            else:
                activated.append(line)  # Keep as comment (it's a real comment)
        else:
            activated.append(line)
    
    # Write activated code
    with open(output_file, 'w') as f:
        f.writelines(activated)
    
    print(f"✅ LangGraph code activated in {output_file}")
    return True

def create_example_workflow():
    """Create an example complex workflow"""
    print("\n📝 Creating example workflow...")
    
    example_file = Path("orchestration/example_langgraph_workflow.py")
    
    example_code = '''"""
Example LangGraph Workflow - Ticket Purchase with Approval

This demonstrates a complex workflow that requires LangGraph.
"""

from orchestration.langgraph_orchestrator import EnterpriseOrchestrator
from typing import Dict, List
import asyncio

async def complex_ticket_purchase():
    """
    Example: Purchase tickets with multi-level approval
    
    Flow:
    1. Check inventory
    2. Calculate price
    3. If > $1000: Get manager approval
    4. If > $5000: Get director approval
    5. Process payment
    6. Send tickets (parallel)
    7. Update CRM (parallel)
    8. Send notifications (parallel)
    """
    
    orchestrator = EnterpriseOrchestrator(
        project_id="your-project-id",
        region="us-central1"
    )
    
    # Initial request
    messages = [
        {"role": "user", "content": "I need 100 tickets for the corporate event"}
    ]
    
    # Execute complex workflow
    result = await orchestrator.execute(messages)
    
    print(f"Workflow completed!")
    print(f"Final state: {result}")
    
    return result

if __name__ == "__main__":
    # Run the example
    asyncio.run(complex_ticket_purchase())
'''
    
    with open(example_file, 'w') as f:
        f.write(example_code)
    
    print(f"✅ Example workflow created: {example_file}")
    return True

def update_imports_guide():
    """Show how to update imports"""
    print("\n📚 Update Your Imports:")
    print("=" * 50)
    print("\nBefore (Simple Coordinator):")
    print("```python")
    print("from orchestration import SimpleCoordinator")
    print("coordinator = SimpleCoordinator()")
    print("```")
    print("\nAfter (LangGraph):")
    print("```python")
    print("from orchestration.langgraph_orchestrator import EnterpriseOrchestrator")
    print("orchestrator = EnterpriseOrchestrator(project_id, region)")
    print("```")

def main():
    """Main activation flow"""
    print("🚀 LangGraph Activation Assistant")
    print("=" * 50)
    
    # Step 1: Check if upgrade is needed
    should_upgrade, reason = check_complexity_needs()
    
    if not should_upgrade:
        print(f"\n💡 {reason}")
        response = input("\nDo you still want to proceed with activation? (y/n): ")
        if response.lower() != 'y':
            print("✅ Keeping Simple Coordinator. Good choice!")
            return
    
    print("\n🎯 Starting LangGraph activation...")
    
    # Step 2: Install dependencies
    response = input("\n1. Install LangGraph dependencies? (y/n): ")
    if response.lower() == 'y':
        if not install_dependencies():
            print("⚠️  Continuing without dependencies...")
    
    # Step 3: Activate code
    response = input("\n2. Activate LangGraph code? (y/n): ")
    if response.lower() == 'y':
        if not activate_langgraph_code():
            print("❌ Activation failed!")
            return
    
    # Step 4: Create example
    response = input("\n3. Create example workflow? (y/n): ")
    if response.lower() == 'y':
        create_example_workflow()
    
    # Step 5: Show import guide
    update_imports_guide()
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ LangGraph Activation Complete!")
    print("\nNext steps:")
    print("1. Review orchestration/langgraph_orchestrator.py")
    print("2. Check orchestration/example_langgraph_workflow.py")
    print("3. Update your imports to use EnterpriseOrchestrator")
    print("4. Test with complex workflows")
    print("\n📖 See LANGGRAPH_UPGRADE_GUIDE.md for detailed documentation")

if __name__ == "__main__":
    main()
