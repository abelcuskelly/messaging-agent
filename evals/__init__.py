"""
Evaluation System for Messaging Agent

Comprehensive evaluation using:
- LLM-as-a-judge (OpenAI GPT-4 or Vertex AI Gemini)
- Domain-specific rule-based checks
- Performance benchmarking
- Regression testing

Usage:
    from evals import EvaluationSuite, LLMJudge, DomainEvaluator
    
    # Run comprehensive evaluation
    suite = EvaluationSuite()
    results = suite.evaluate_batch(test_cases)
    report = suite.generate_report(results)
    
    # Use LLM judge alone
    judge = LLMJudge()
    result = judge.evaluate_response(user_msg, agent_response)
    
    # Use domain checks alone
    evaluator = DomainEvaluator()
    result = evaluator.evaluate(user_msg, agent_response)
"""

from evals.llm_judge import LLMJudge, EvalResult, TICKETING_EVAL_CASES
from evals.domain_specific import (
    DomainEvaluator,
    PriceAccuracyChecker,
    InventoryValidationChecker,
    OrderFlowChecker,
    PolicyComplianceChecker,
    ToolUsageChecker,
    DomainEvalResult,
    DOMAIN_TEST_CASES
)
from evals.eval_suite import EvaluationSuite, ComprehensiveEvalResult, run_full_evaluation
from evals.pipeline_integration import PipelineEvaluator, create_standard_test_cases

__all__ = [
    # Main classes
    'EvaluationSuite',
    'LLMJudge',
    'DomainEvaluator',
    'PipelineEvaluator',
    
    # Result types
    'EvalResult',
    'DomainEvalResult',
    'ComprehensiveEvalResult',
    
    # Domain checkers
    'PriceAccuracyChecker',
    'InventoryValidationChecker',
    'OrderFlowChecker',
    'PolicyComplianceChecker',
    'ToolUsageChecker',
    
    # Test cases
    'TICKETING_EVAL_CASES',
    'DOMAIN_TEST_CASES',
    'create_standard_test_cases',
    
    # Utilities
    'run_full_evaluation'
]

__version__ = '1.0.0'
