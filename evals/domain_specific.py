"""
Domain-Specific Evaluations for Ticketing Agent

Rule-based evaluations specific to ticketing workflows:
- Price accuracy
- Inventory validation
- Order flow correctness
- Policy compliance
- Tool usage patterns
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DomainEvalResult:
    """Result from domain-specific evaluation"""
    passed: bool
    score: float
    checks_passed: int
    checks_failed: int
    issues: List[str]
    warnings: List[str]
    category: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class PriceAccuracyChecker:
    """Validate price accuracy in agent responses"""
    
    def check(self, 
             response: str,
             expected_prices: Optional[Dict[str, float]] = None) -> DomainEvalResult:
        """
        Check if prices mentioned in response are accurate
        
        Args:
            response: Agent response text
            expected_prices: Dictionary of {item: expected_price}
        
        Returns:
            DomainEvalResult
        """
        issues = []
        warnings = []
        checks_passed = 0
        checks_failed = 0
        
        # Extract prices from response
        price_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        found_prices = re.findall(price_pattern, response)
        
        # Check 1: Prices are formatted correctly
        if found_prices:
            checks_passed += 1
        else:
            if expected_prices:
                issues.append("No prices found in response when prices were expected")
                checks_failed += 1
        
        # Check 2: Prices match expected values
        if expected_prices:
            for item, expected_price in expected_prices.items():
                if item.lower() in response.lower():
                    # Find associated price
                    found = False
                    for price_str in found_prices:
                        price = float(price_str.replace(',', ''))
                        if abs(price - expected_price) < 0.01:
                            checks_passed += 1
                            found = True
                            break
                    
                    if not found:
                        issues.append(f"Price mismatch for {item}: expected ${expected_price}")
                        checks_failed += 1
        
        # Check 3: Total calculations are correct
        if 'total' in response.lower() or '×' in response or 'x' in response:
            # Try to verify multiplication
            mult_pattern = r'\$?(\d+)\s*[×x]\s*(\d+)\s*=\s*\$?(\d+)'
            multiplications = re.findall(mult_pattern, response, re.IGNORECASE)
            
            for price, qty, total in multiplications:
                expected_total = int(price) * int(qty)
                actual_total = int(total)
                
                if expected_total == actual_total:
                    checks_passed += 1
                else:
                    issues.append(f"Math error: ${price} × {qty} = ${actual_total} (should be ${expected_total})")
                    checks_failed += 1
        
        # Calculate score
        total_checks = checks_passed + checks_failed
        score = checks_passed / total_checks if total_checks > 0 else 1.0
        
        return DomainEvalResult(
            passed=len(issues) == 0,
            score=score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            issues=issues,
            warnings=warnings,
            category="price_accuracy"
        )


class InventoryValidationChecker:
    """Validate inventory and availability claims"""
    
    def check(self,
             response: str,
             actual_inventory: Optional[Dict[str, int]] = None) -> DomainEvalResult:
        """
        Check if inventory claims are valid
        
        Args:
            response: Agent response
            actual_inventory: Actual available inventory
        
        Returns:
            DomainEvalResult
        """
        issues = []
        warnings = []
        checks_passed = 0
        checks_failed = 0
        
        # Check 1: Doesn't promise unavailable seats
        if actual_inventory:
            for section, available in actual_inventory.items():
                if section.lower() in response.lower():
                    # Check if agent claims availability
                    if available == 0 and 'available' in response.lower():
                        issues.append(f"Claims {section} available but inventory shows 0")
                        checks_failed += 1
                    else:
                        checks_passed += 1
        
        # Check 2: Mentions sold out if applicable
        if actual_inventory and any(v == 0 for v in actual_inventory.values()):
            if 'sold out' in response.lower() or 'not available' in response.lower():
                checks_passed += 1
            else:
                warnings.append("Some sections sold out but not mentioned")
        
        # Check 3: Quantity constraints
        quantity_pattern = r'(\d+)\s+(?:ticket|seat)s?\s+available'
        quantities = re.findall(quantity_pattern, response, re.IGNORECASE)
        
        for qty_str in quantities:
            qty = int(qty_str)
            if qty > 0:
                checks_passed += 1
            else:
                issues.append(f"Invalid quantity: {qty}")
                checks_failed += 1
        
        # Calculate score
        total_checks = checks_passed + checks_failed
        score = checks_passed / total_checks if total_checks > 0 else 1.0
        
        return DomainEvalResult(
            passed=len(issues) == 0,
            score=score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            issues=issues,
            warnings=warnings,
            category="inventory_validation"
        )


class OrderFlowChecker:
    """Validate order flow correctness"""
    
    def check(self,
             conversation: List[Dict[str, str]],
             expected_flow: List[str]) -> DomainEvalResult:
        """
        Check if conversation follows correct order flow
        
        Args:
            conversation: List of messages
            expected_flow: Expected steps (e.g., ['search', 'select', 'hold', 'payment', 'confirm'])
        
        Returns:
            DomainEvalResult
        """
        issues = []
        warnings = []
        checks_passed = 0
        checks_failed = 0
        
        # Extract flow from conversation
        actual_flow = []
        for msg in conversation:
            if msg['role'] == 'assistant':
                content = msg['content'].lower()
                
                if any(word in content for word in ['available', 'section', 'price']):
                    actual_flow.append('search')
                elif 'hold' in content or 'reserved' in content:
                    actual_flow.append('hold')
                elif 'payment' in content or 'credit card' in content:
                    actual_flow.append('payment')
                elif 'confirmed' in content or 'order #' in content:
                    actual_flow.append('confirm')
        
        # Check flow order
        expected_idx = 0
        for step in actual_flow:
            if expected_idx < len(expected_flow) and step == expected_flow[expected_idx]:
                checks_passed += 1
                expected_idx += 1
            else:
                # Out of order
                if step in expected_flow:
                    issues.append(f"Step '{step}' out of order")
                    checks_failed += 1
        
        # Check for missing steps
        for expected_step in expected_flow:
            if expected_step not in actual_flow:
                warnings.append(f"Missing step: {expected_step}")
        
        # Calculate score
        total_checks = checks_passed + checks_failed
        score = checks_passed / total_checks if total_checks > 0 else 1.0
        
        return DomainEvalResult(
            passed=len(issues) == 0,
            score=score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            issues=issues,
            warnings=warnings,
            category="order_flow"
        )


class PolicyComplianceChecker:
    """Validate policy compliance in responses"""
    
    def __init__(self):
        # Define ticketing policies
        self.policies = {
            "refund_window": 48,  # hours before event
            "max_tickets_per_order": 8,
            "hold_duration": 300,  # seconds
            "upgrade_cutoff": 2  # hours before event
        }
    
    def check(self, response: str, action: str) -> DomainEvalResult:
        """
        Check if response follows policies
        
        Args:
            response: Agent response
            action: Action type (refund, purchase, upgrade)
        
        Returns:
            DomainEvalResult
        """
        issues = []
        warnings = []
        checks_passed = 0
        checks_failed = 0
        
        # Check refund policy
        if action == 'refund':
            if 'policy' in response.lower() or '48 hour' in response.lower():
                checks_passed += 1
            else:
                warnings.append("Refund policy not mentioned")
            
            if 'refund' in response.lower():
                checks_passed += 1
            else:
                issues.append("No refund confirmation")
                checks_failed += 1
        
        # Check purchase limits
        if action == 'purchase':
            quantity_pattern = r'(\d+)\s+ticket'
            quantities = re.findall(quantity_pattern, response, re.IGNORECASE)
            
            for qty_str in quantities:
                qty = int(qty_str)
                if qty <= self.policies['max_tickets_per_order']:
                    checks_passed += 1
                else:
                    issues.append(f"Quantity {qty} exceeds max {self.policies['max_tickets_per_order']}")
                    checks_failed += 1
        
        # Check hold duration mentioned
        if 'hold' in response.lower():
            if '5 minute' in response.lower() or '300' in response:
                checks_passed += 1
            else:
                warnings.append("Hold duration not clearly stated")
        
        # Calculate score
        total_checks = checks_passed + checks_failed
        score = checks_passed / total_checks if total_checks > 0 else 1.0
        
        return DomainEvalResult(
            passed=len(issues) == 0,
            score=score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            issues=issues,
            warnings=warnings,
            category="policy_compliance"
        )


class ToolUsageChecker:
    """Validate appropriate tool usage"""
    
    def __init__(self):
        # Define expected tools for each intent
        self.intent_to_tools = {
            "search": ["get_event_info", "check_inventory"],
            "purchase": ["check_inventory", "hold_tickets", "create_order"],
            "upgrade": ["get_order", "check_inventory", "upgrade_tickets"],
            "refund": ["get_order", "check_policy", "process_refund"],
            "inquiry": ["get_event_info"]
        }
    
    def check(self,
             user_message: str,
             tools_used: List[str],
             tools_available: List[str]) -> DomainEvalResult:
        """
        Check if correct tools were used
        
        Args:
            user_message: User's message
            tools_used: Tools the agent actually used
            tools_available: Tools that were available
        
        Returns:
            DomainEvalResult
        """
        issues = []
        warnings = []
        checks_passed = 0
        checks_failed = 0
        
        # Detect intent
        intent = self._detect_intent(user_message)
        expected_tools = self.intent_to_tools.get(intent, [])
        
        # Check if essential tools were used
        for tool in expected_tools:
            if tool in tools_used:
                checks_passed += 1
            elif tool in tools_available:
                issues.append(f"Should have used tool: {tool}")
                checks_failed += 1
        
        # Check for unnecessary tools
        for tool in tools_used:
            if tool not in expected_tools and expected_tools:
                warnings.append(f"Unexpected tool used: {tool}")
        
        # Check if no tools used when they should be
        if expected_tools and not tools_used:
            issues.append(f"No tools used for {intent} intent (expected: {expected_tools})")
            checks_failed += 1
        
        # Calculate score
        total_checks = checks_passed + checks_failed
        score = checks_passed / total_checks if total_checks > 0 else 1.0
        
        return DomainEvalResult(
            passed=len(issues) == 0,
            score=score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            issues=issues,
            warnings=warnings,
            category="tool_usage"
        )
    
    def _detect_intent(self, user_message: str) -> str:
        """Detect user intent from message"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['buy', 'purchase', 'need', 'want']):
            return 'purchase'
        elif any(word in message_lower for word in ['upgrade', 'better seat']):
            return 'upgrade'
        elif any(word in message_lower for word in ['refund', 'cancel', 'return']):
            return 'refund'
        elif any(word in message_lower for word in ['search', 'find', 'available']):
            return 'search'
        else:
            return 'inquiry'


class DomainEvaluator:
    """
    Comprehensive domain-specific evaluator
    
    Combines all domain checkers for complete validation
    """
    
    def __init__(self):
        self.price_checker = PriceAccuracyChecker()
        self.inventory_checker = InventoryValidationChecker()
        self.order_flow_checker = OrderFlowChecker()
        self.policy_checker = PolicyComplianceChecker()
        self.tool_usage_checker = ToolUsageChecker()
    
    def evaluate(self,
                user_message: str,
                agent_response: str,
                tools_used: List[str] = None,
                conversation_history: List[Dict] = None,
                expected_prices: Dict[str, float] = None,
                actual_inventory: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Run all domain-specific checks
        
        Returns:
            Comprehensive evaluation results
        """
        results = {}
        
        # Run all checkers
        results['price_accuracy'] = self.price_checker.check(
            agent_response,
            expected_prices
        )
        
        results['inventory_validation'] = self.inventory_checker.check(
            agent_response,
            actual_inventory
        )
        
        if conversation_history:
            results['order_flow'] = self.order_flow_checker.check(
                conversation_history,
                expected_flow=['search', 'hold', 'payment', 'confirm']
            )
        
        # Detect action for policy check
        action = 'purchase'
        if 'refund' in user_message.lower():
            action = 'refund'
        elif 'upgrade' in user_message.lower():
            action = 'upgrade'
        
        results['policy_compliance'] = self.policy_checker.check(
            agent_response,
            action
        )
        
        if tools_used is not None:
            results['tool_usage'] = self.tool_usage_checker.check(
                user_message,
                tools_used,
                tools_available=['get_event_info', 'check_inventory', 'hold_tickets', 
                               'create_order', 'upgrade_tickets', 'process_refund']
            )
        
        # Calculate overall domain score
        scores = [r.score for r in results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        passed_checks = sum(r.checks_passed for r in results.values())
        failed_checks = sum(r.checks_failed for r in results.values())
        
        all_issues = []
        all_warnings = []
        for r in results.values():
            all_issues.extend(r.issues)
            all_warnings.extend(r.warnings)
        
        return {
            "overall_score": overall_score,
            "passed": len(all_issues) == 0,
            "checks_passed": passed_checks,
            "checks_failed": failed_checks,
            "issues": all_issues,
            "warnings": all_warnings,
            "detailed_results": {k: asdict(v) for k, v in results.items()}
        }


# Example test cases
DOMAIN_TEST_CASES = [
    {
        "name": "Price accuracy - correct math",
        "user_message": "2 tickets in Section B",
        "agent_response": "Perfect! Section B tickets are $180 each. For 2 tickets: $180 × 2 = $360 total.",
        "expected_prices": {"Section B": 180.00},
        "should_pass": True
    },
    {
        "name": "Price accuracy - incorrect math",
        "user_message": "2 tickets in Section B",
        "agent_response": "Perfect! Section B tickets are $180 each. For 2 tickets: $180 × 2 = $400 total.",
        "expected_prices": {"Section B": 180.00},
        "should_pass": False
    },
    {
        "name": "Inventory validation - correct",
        "user_message": "Are Section A tickets available?",
        "agent_response": "Yes! Section A has 5 tickets available in Row 3.",
        "actual_inventory": {"Section A": 5},
        "should_pass": True
    },
    {
        "name": "Inventory validation - incorrect",
        "user_message": "Are Section A tickets available?",
        "agent_response": "Yes! Section A has tickets available.",
        "actual_inventory": {"Section A": 0},
        "should_pass": False
    }
]


def run_domain_evaluation():
    """Run domain-specific evaluation demo"""
    print("🎯 Domain-Specific Evaluation Demo")
    print("=" * 60)
    
    evaluator = DomainEvaluator()
    
    print(f"\n📋 Running {len(DOMAIN_TEST_CASES)} domain-specific tests...\n")
    
    for i, test_case in enumerate(DOMAIN_TEST_CASES, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"  User: {test_case['user_message']}")
        print(f"  Agent: {test_case['agent_response'][:80]}...")
        
        result = evaluator.evaluate(
            user_message=test_case['user_message'],
            agent_response=test_case['agent_response'],
            expected_prices=test_case.get('expected_prices'),
            actual_inventory=test_case.get('actual_inventory')
        )
        
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  Result: {status} (Score: {result['overall_score']:.2f})")
        
        if result['issues']:
            print(f"  Issues: {', '.join(result['issues'])}")
        if result['warnings']:
            print(f"  Warnings: {', '.join(result['warnings'])}")
        
        print()
    
    print("=" * 60)
    print("✅ Domain evaluation complete!")


if __name__ == "__main__":
    run_domain_evaluation()
