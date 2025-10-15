"""
Comprehensive Evaluation Suite

Combines LLM-as-a-judge with domain-specific checks for complete evaluation.

Evaluation Layers:
1. Rule-based domain checks (fast, deterministic)
2. LLM-as-a-judge (comprehensive, nuanced)
3. Performance metrics (speed, cost)
4. Regression testing (prevent degradation)
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
import time

from evals.llm_judge import LLMJudge, EvalResult, TICKETING_EVAL_CASES
from evals.domain_specific import DomainEvaluator, DOMAIN_TEST_CASES

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveEvalResult:
    """Combined result from all evaluation layers"""
    test_case_name: str
    llm_eval: Optional[EvalResult]
    domain_eval: Optional[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    overall_passed: bool
    overall_score: float
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class EvaluationSuite:
    """
    Comprehensive evaluation suite for messaging agent
    
    Features:
    - LLM-as-a-judge evaluation (OpenAI GPT-4)
    - Domain-specific rule-based checks
    - Performance benchmarking
    - Regression testing
    - Batch evaluation
    - Detailed reporting
    """
    
    def __init__(self, 
                 use_llm_judge: bool = True,
                 use_domain_checks: bool = True,
                 llm_provider: str = 'openai'):
        self.use_llm_judge = use_llm_judge
        self.use_domain_checks = use_domain_checks
        
        # Initialize evaluators
        self.llm_judge = None
        if use_llm_judge:
            try:
                self.llm_judge = LLMJudge(provider=llm_provider)
                logger.info("LLM judge initialized")
            except Exception as e:
                logger.warning(f"LLM judge initialization failed: {e}")
                self.use_llm_judge = False
        
        self.domain_evaluator = None
        if use_domain_checks:
            self.domain_evaluator = DomainEvaluator()
            logger.info("Domain evaluator initialized")
    
    def evaluate_single(self,
                       test_case: Dict[str, Any]) -> ComprehensiveEvalResult:
        """
        Evaluate a single test case with all enabled evaluators
        
        Args:
            test_case: Test case with user_message, agent_response, etc.
        
        Returns:
            ComprehensiveEvalResult
        """
        start_time = time.time()
        
        # Extract test case data
        user_message = test_case.get('user_message', '')
        agent_response = test_case.get('agent_response', '')
        tools_used = test_case.get('tools_used', [])
        context = test_case.get('context')
        
        # LLM evaluation
        llm_result = None
        if self.use_llm_judge and self.llm_judge:
            try:
                llm_result = self.llm_judge.evaluate_response(
                    user_message=user_message,
                    agent_response=agent_response,
                    context=context,
                    tools_used=tools_used
                )
            except Exception as e:
                logger.error(f"LLM evaluation failed: {e}")
        
        # Domain evaluation
        domain_result = None
        if self.use_domain_checks and self.domain_evaluator:
            try:
                domain_result = self.domain_evaluator.evaluate(
                    user_message=user_message,
                    agent_response=agent_response,
                    tools_used=tools_used,
                    expected_prices=test_case.get('expected_prices'),
                    actual_inventory=test_case.get('actual_inventory')
                )
            except Exception as e:
                logger.error(f"Domain evaluation failed: {e}")
        
        # Performance metrics
        eval_time = (time.time() - start_time) * 1000
        performance_metrics = {
            "eval_time_ms": eval_time,
            "response_length": len(agent_response),
            "tools_count": len(tools_used) if tools_used else 0
        }
        
        # Calculate overall score and pass/fail
        scores = []
        if llm_result:
            scores.append(llm_result.overall_score)
        if domain_result:
            scores.append(domain_result['overall_score'])
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        # Pass criteria: both evaluators pass (if enabled)
        overall_passed = True
        if llm_result:
            overall_passed = overall_passed and llm_result.passed
        if domain_result:
            overall_passed = overall_passed and domain_result['passed']
        
        return ComprehensiveEvalResult(
            test_case_name=test_case.get('name', 'Unnamed test'),
            llm_eval=llm_result,
            domain_eval=domain_result,
            performance_metrics=performance_metrics,
            overall_passed=overall_passed,
            overall_score=overall_score
        )
    
    def evaluate_batch(self, test_cases: List[Dict[str, Any]]) -> List[ComprehensiveEvalResult]:
        """
        Evaluate multiple test cases
        
        Args:
            test_cases: List of test cases
        
        Returns:
            List of ComprehensiveEvalResults
        """
        results = []
        
        logger.info(f"Starting batch evaluation of {len(test_cases)} test cases")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Evaluating test case {i}/{len(test_cases)}: {test_case.get('name')}")
            
            result = self.evaluate_single(test_case)
            results.append(result)
        
        logger.info(f"Batch evaluation complete: {len(results)} cases evaluated")
        
        return results
    
    def generate_report(self, results: List[ComprehensiveEvalResult]) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report
        
        Args:
            results: List of evaluation results
        
        Returns:
            Detailed report with statistics and recommendations
        """
        if not results:
            return {"error": "No results to analyze"}
        
        # Overall statistics
        total_cases = len(results)
        passed_cases = sum(1 for r in results if r.overall_passed)
        pass_rate = passed_cases / total_cases
        
        # Score statistics
        overall_scores = [r.overall_score for r in results]
        avg_overall_score = sum(overall_scores) / len(overall_scores)
        min_score = min(overall_scores)
        max_score = max(overall_scores)
        
        # LLM judge statistics
        llm_stats = None
        if any(r.llm_eval for r in results):
            llm_results = [r.llm_eval for r in results if r.llm_eval]
            llm_stats = {
                "avg_helpfulness": sum(r.helpfulness for r in llm_results) / len(llm_results),
                "avg_accuracy": sum(r.accuracy for r in llm_results) / len(llm_results),
                "avg_appropriateness": sum(r.appropriateness for r in llm_results) / len(llm_results),
                "avg_tool_usage": sum(r.tool_usage for r in llm_results) / len(llm_results),
                "avg_conversation_flow": sum(r.conversation_flow for r in llm_results) / len(llm_results),
                "avg_domain_expertise": sum(r.domain_expertise for r in llm_results) / len(llm_results)
            }
        
        # Domain check statistics
        domain_stats = None
        if any(r.domain_eval for r in results):
            domain_results = [r.domain_eval for r in results if r.domain_eval]
            domain_stats = {
                "total_checks": sum(r['checks_passed'] + r['checks_failed'] for r in domain_results),
                "checks_passed": sum(r['checks_passed'] for r in domain_results),
                "checks_failed": sum(r['checks_failed'] for r in domain_results),
                "check_pass_rate": sum(r['checks_passed'] for r in domain_results) / max(sum(r['checks_passed'] + r['checks_failed'] for r in domain_results), 1)
            }
        
        # Performance statistics
        avg_eval_time = sum(r.performance_metrics['eval_time_ms'] for r in results) / len(results)
        
        # Find failing cases
        failing_cases = [
            {
                "name": r.test_case_name,
                "score": r.overall_score,
                "issues": r.domain_eval['issues'] if r.domain_eval else [],
                "llm_feedback": r.llm_eval.feedback if r.llm_eval else None
            }
            for r in results if not r.overall_passed
        ]
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            pass_rate, 
            avg_overall_score, 
            llm_stats, 
            domain_stats
        )
        
        return {
            "summary": {
                "total_cases": total_cases,
                "passed": passed_cases,
                "failed": total_cases - passed_cases,
                "pass_rate": pass_rate,
                "avg_overall_score": avg_overall_score,
                "min_score": min_score,
                "max_score": max_score
            },
            "llm_judge_stats": llm_stats,
            "domain_check_stats": domain_stats,
            "performance": {
                "avg_eval_time_ms": avg_eval_time
            },
            "failing_cases": failing_cases,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_recommendation(self,
                                pass_rate: float,
                                avg_score: float,
                                llm_stats: Optional[Dict],
                                domain_stats: Optional[Dict]) -> str:
        """Generate deployment recommendation"""
        
        if pass_rate >= 0.95 and avg_score >= 0.90:
            return "✅ READY FOR PRODUCTION - Excellent performance on all evaluations"
        
        elif pass_rate >= 0.90 and avg_score >= 0.85:
            return "✅ READY FOR PRODUCTION - Good performance, minor improvements possible"
        
        elif pass_rate >= 0.80 and avg_score >= 0.75:
            return "⚠️ READY WITH CAUTION - Deploy to staging first, monitor closely"
        
        elif pass_rate >= 0.70:
            return "🔧 NEEDS IMPROVEMENT - Fix failing cases before production deployment"
        
        else:
            return "❌ NOT READY - Significant issues, requires retraining or prompt engineering"
    
    def save_results(self, 
                    results: List[ComprehensiveEvalResult],
                    report: Dict[str, Any],
                    output_file: str = "eval_results.json"):
        """Save evaluation results to file"""
        output = {
            "test_results": [asdict(r) for r in results],
            "report": report,
            "metadata": {
                "evaluator_config": {
                    "llm_judge_enabled": self.use_llm_judge,
                    "domain_checks_enabled": self.use_domain_checks
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_file}")
        return output_file


def run_full_evaluation():
    """Run complete evaluation suite"""
    print("🔬 COMPREHENSIVE EVALUATION SUITE")
    print("=" * 80)
    
    # Initialize suite
    suite = EvaluationSuite(
        use_llm_judge=True,
        use_domain_checks=True,
        llm_provider='openai'
    )
    
    print(f"\n✅ Configuration:")
    print(f"   LLM Judge: {'Enabled' if suite.use_llm_judge else 'Disabled'}")
    print(f"   Domain Checks: {'Enabled' if suite.use_domain_checks else 'Disabled'}")
    
    # Combine test cases
    all_test_cases = []
    
    # Add LLM test cases
    for case in TICKETING_EVAL_CASES:
        all_test_cases.append({
            "name": case['name'],
            "user_message": case['user_message'],
            "agent_response": case['agent_response'],
            "tools_used": case.get('tools_used'),
            "expected_score": case.get('expected_score')
        })
    
    # Add domain test cases
    for case in DOMAIN_TEST_CASES:
        all_test_cases.append({
            "name": case['name'],
            "user_message": case['user_message'],
            "agent_response": case['agent_response'],
            "expected_prices": case.get('expected_prices'),
            "actual_inventory": case.get('actual_inventory')
        })
    
    print(f"\n📋 Evaluating {len(all_test_cases)} test cases...\n")
    
    # Run evaluation
    results = suite.evaluate_batch(all_test_cases)
    
    # Generate report
    print("\n" + "=" * 80)
    print("📊 EVALUATION REPORT")
    print("=" * 80)
    
    report = suite.generate_report(results)
    
    # Display summary
    print(f"\n✅ Summary:")
    print(f"   Total cases: {report['summary']['total_cases']}")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Pass rate: {report['summary']['pass_rate']:.1%}")
    print(f"   Avg score: {report['summary']['avg_overall_score']:.2f}")
    
    if report.get('llm_judge_stats'):
        print(f"\n🤖 LLM Judge Stats:")
        for metric, value in report['llm_judge_stats'].items():
            print(f"   {metric:25s}: {value:.2f}")
    
    if report.get('domain_check_stats'):
        print(f"\n🎯 Domain Check Stats:")
        for metric, value in report['domain_check_stats'].items():
            print(f"   {metric:25s}: {value if isinstance(value, int) else f'{value:.2f}'}")
    
    print(f"\n⚡ Performance:")
    print(f"   Avg eval time: {report['performance']['avg_eval_time_ms']:.0f}ms")
    
    # Show failing cases
    if report['failing_cases']:
        print(f"\n❌ Failing Cases ({len(report['failing_cases'])}):")
        for case in report['failing_cases'][:3]:
            print(f"\n   {case['name']} (Score: {case['score']:.2f})")
            if case['issues']:
                print(f"   Issues: {', '.join(case['issues'][:2])}")
            if case['llm_feedback']:
                print(f"   Feedback: {case['llm_feedback'][:100]}...")
    
    print(f"\n💡 Recommendation:")
    print(f"   {report['recommendation']}")
    
    # Save results
    output_file = suite.save_results(results, report)
    print(f"\n📁 Full results saved to: {output_file}")
    
    return report


if __name__ == "__main__":
    run_full_evaluation()
