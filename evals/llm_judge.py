"""
LLM-as-a-Judge Evaluator

Uses OpenAI GPT-4 (or Vertex AI Gemini) to evaluate agent responses
with natural language grading and domain-specific criteria.

Evaluation Dimensions:
- Helpfulness
- Accuracy
- Appropriateness
- Tool usage
- Conversation flow
- Domain expertise (ticketing)
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import logging
from datetime import datetime

# OpenAI import
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Vertex AI import (alternative)
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
    HAS_VERTEX_AI = True
except ImportError:
    HAS_VERTEX_AI = False

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Result from LLM evaluation"""
    overall_score: float  # 0.0 to 1.0
    helpfulness: float
    accuracy: float
    appropriateness: float
    tool_usage: float
    conversation_flow: float
    domain_expertise: float
    passed: bool
    feedback: str
    reasoning: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class LLMJudge:
    """
    LLM-as-a-Judge evaluator using OpenAI or Vertex AI
    
    Modes:
    - OpenAI: Uses GPT-4 (recommended for best evaluation quality)
    - Vertex AI: Uses Gemini Pro (for Google Cloud consistency)
    
    Environment Variables:
    - OPENAI_API_KEY: OpenAI API key (for OpenAI mode)
    - EVAL_MODEL: Model to use (default: gpt-4-turbo-preview)
    - EVAL_PROVIDER: 'openai' or 'vertexai' (default: openai)
    """
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or os.getenv('EVAL_PROVIDER', 'openai')
        self.model = model or os.getenv('EVAL_MODEL', 'gpt-4-turbo-preview')
        
        if self.provider == 'openai':
            if not HAS_OPENAI:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.client = OpenAI(api_key=api_key)
            logger.info(f"LLM Judge initialized with OpenAI ({self.model})")
        
        elif self.provider == 'vertexai':
            if not HAS_VERTEX_AI:
                raise ImportError("Vertex AI package not installed")
            
            self.model = GenerativeModel('gemini-pro')
            logger.info("LLM Judge initialized with Vertex AI (Gemini Pro)")
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def evaluate_response(self,
                         user_message: str,
                         agent_response: str,
                         context: Optional[Dict[str, Any]] = None,
                         tools_used: Optional[List[str]] = None) -> EvalResult:
        """
        Evaluate an agent response using LLM-as-a-judge
        
        Args:
            user_message: User's input message
            agent_response: Agent's response to evaluate
            context: Additional context (conversation history, user data)
            tools_used: List of tools the agent used
        
        Returns:
            EvalResult with scores and feedback
        """
        # Build evaluation prompt
        eval_prompt = self._build_eval_prompt(
            user_message, 
            agent_response, 
            context, 
            tools_used
        )
        
        # Get LLM evaluation
        if self.provider == 'openai':
            eval_response = self._evaluate_with_openai(eval_prompt)
        else:
            eval_response = self._evaluate_with_vertexai(eval_prompt)
        
        # Parse evaluation
        result = self._parse_eval_response(eval_response)
        
        logger.info(
            "LLM evaluation complete",
            overall_score=result.overall_score,
            passed=result.passed
        )
        
        return result
    
    def _build_eval_prompt(self,
                          user_message: str,
                          agent_response: str,
                          context: Optional[Dict] = None,
                          tools_used: Optional[List[str]] = None) -> str:
        """Build the evaluation prompt for the LLM judge"""
        
        prompt = f"""You are an expert evaluator for an AI ticketing assistant. Your job is to grade the agent's response on multiple dimensions.

**Context:**
This is a text-to-buy ticketing system where customers purchase and upgrade sports tickets via natural conversation.

**User Message:**
{user_message}

**Agent Response:**
{agent_response}
"""
        
        if tools_used:
            prompt += f"\n**Tools Used:**\n{', '.join(tools_used)}\n"
        
        if context:
            prompt += f"\n**Additional Context:**\n{json.dumps(context, indent=2)}\n"
        
        prompt += """
**Evaluation Criteria:**

Grade the response on each dimension (0.0 to 1.0):

1. **Helpfulness** (0.0 - 1.0)
   - Does the response help the customer achieve their goal?
   - Is it actionable and clear?
   - Does it provide the information needed?

2. **Accuracy** (0.0 - 1.0)
   - Is the information correct?
   - Are prices, dates, and details accurate?
   - Does it avoid hallucinations?

3. **Appropriateness** (0.0 - 1.0)
   - Is the tone professional yet friendly?
   - Is the response length appropriate?
   - Does it match the context?

4. **Tool Usage** (0.0 - 1.0)
   - Were the right tools used?
   - Should any tools have been used but weren't?
   - Were tools used efficiently?

5. **Conversation Flow** (0.0 - 1.0)
   - Does the response flow naturally?
   - Does it maintain context from earlier messages?
   - Does it guide the customer to next steps?

6. **Domain Expertise** (0.0 - 1.0)
   - Does it demonstrate knowledge of ticketing?
   - Are policies and procedures followed?
   - Does it handle edge cases well?

**Output Format (JSON):**
```json
{
  "helpfulness": 0.95,
  "accuracy": 0.90,
  "appropriateness": 0.85,
  "tool_usage": 0.90,
  "conversation_flow": 0.95,
  "domain_expertise": 0.88,
  "overall_score": 0.90,
  "passed": true,
  "feedback": "Brief summary of strengths and weaknesses",
  "reasoning": "Detailed explanation of the scores"
}
```

Provide ONLY the JSON output, no additional text.
"""
        
        return prompt
    
    def _evaluate_with_openai(self, prompt: str) -> str:
        """Evaluate using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent grading
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"OpenAI evaluation error: {e}")
            raise
    
    def _evaluate_with_vertexai(self, prompt: str) -> str:
        """Evaluate using Vertex AI Gemini"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            logger.error(f"Vertex AI evaluation error: {e}")
            raise
    
    def _parse_eval_response(self, response: str) -> EvalResult:
        """Parse LLM evaluation response into EvalResult"""
        try:
            # Parse JSON response
            eval_data = json.loads(response)
            
            # Create EvalResult
            result = EvalResult(
                overall_score=eval_data.get('overall_score', 0.0),
                helpfulness=eval_data.get('helpfulness', 0.0),
                accuracy=eval_data.get('accuracy', 0.0),
                appropriateness=eval_data.get('appropriateness', 0.0),
                tool_usage=eval_data.get('tool_usage', 0.0),
                conversation_flow=eval_data.get('conversation_flow', 0.0),
                domain_expertise=eval_data.get('domain_expertise', 0.0),
                passed=eval_data.get('passed', False),
                feedback=eval_data.get('feedback', ''),
                reasoning=eval_data.get('reasoning', '')
            )
            
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse eval response: {e}")
            logger.error(f"Response was: {response}")
            
            # Return failed evaluation
            return EvalResult(
                overall_score=0.0,
                helpfulness=0.0,
                accuracy=0.0,
                appropriateness=0.0,
                tool_usage=0.0,
                conversation_flow=0.0,
                domain_expertise=0.0,
                passed=False,
                feedback="Evaluation parsing failed",
                reasoning=str(e)
            )
    
    def evaluate_batch(self,
                      test_cases: List[Dict[str, Any]],
                      parallel: bool = True) -> List[EvalResult]:
        """
        Evaluate multiple test cases
        
        Args:
            test_cases: List of test cases with user_message and agent_response
            parallel: Whether to evaluate in parallel (faster but more API calls)
        
        Returns:
            List of EvalResults
        """
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Evaluating test case {i}/{len(test_cases)}")
            
            result = self.evaluate_response(
                user_message=test_case.get('user_message', ''),
                agent_response=test_case.get('agent_response', ''),
                context=test_case.get('context'),
                tools_used=test_case.get('tools_used')
            )
            
            results.append(result)
        
        return results
    
    def generate_eval_report(self, results: List[EvalResult]) -> Dict[str, Any]:
        """
        Generate summary report from evaluation results
        
        Args:
            results: List of EvalResults
        
        Returns:
            Summary statistics and report
        """
        if not results:
            return {"error": "No results to analyze"}
        
        # Calculate averages
        avg_scores = {
            "overall_score": sum(r.overall_score for r in results) / len(results),
            "helpfulness": sum(r.helpfulness for r in results) / len(results),
            "accuracy": sum(r.accuracy for r in results) / len(results),
            "appropriateness": sum(r.appropriateness for r in results) / len(results),
            "tool_usage": sum(r.tool_usage for r in results) / len(results),
            "conversation_flow": sum(r.conversation_flow for r in results) / len(results),
            "domain_expertise": sum(r.domain_expertise for r in results) / len(results)
        }
        
        # Pass rate
        passed_count = sum(1 for r in results if r.passed)
        pass_rate = passed_count / len(results)
        
        # Find weakest areas
        weakest_dimension = min(avg_scores.items(), key=lambda x: x[1] if x[0] != 'overall_score' else 1.0)
        
        # Collect common issues
        all_feedback = [r.feedback for r in results if r.feedback]
        
        return {
            "total_evaluated": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
            "pass_rate": pass_rate,
            "average_scores": avg_scores,
            "weakest_dimension": {
                "name": weakest_dimension[0],
                "score": weakest_dimension[1]
            },
            "feedback_summary": all_feedback[:5],  # Top 5 feedback items
            "recommendation": self._generate_recommendation(avg_scores, pass_rate)
        }
    
    def _generate_recommendation(self, 
                                avg_scores: Dict[str, float],
                                pass_rate: float) -> str:
        """Generate recommendation based on eval results"""
        
        if pass_rate >= 0.95 and avg_scores['overall_score'] >= 0.90:
            return "✅ READY FOR PRODUCTION - Excellent performance across all dimensions"
        
        elif pass_rate >= 0.85 and avg_scores['overall_score'] >= 0.80:
            return "⚠️ READY WITH MONITORING - Good performance, monitor weakest areas"
        
        elif pass_rate >= 0.70:
            return "🔧 NEEDS IMPROVEMENT - Address failing test cases before production"
        
        else:
            return "❌ NOT READY - Significant issues found, requires additional training"


# Example test cases for ticketing domain
TICKETING_EVAL_CASES = [
    {
        "name": "Simple ticket purchase",
        "user_message": "I need 2 tickets for tonight's Lakers game",
        "agent_response": "Great! I found tonight's Lakers vs Warriors game at 7:00 PM. Available sections: Section A ($250/seat), Section B ($180/seat), Section C ($85/seat). How many tickets would you like?",
        "tools_used": ["get_event_info", "check_inventory"],
        "expected_score": 0.90
    },
    {
        "name": "Seat upgrade request",
        "user_message": "Can I upgrade my seats to a better section?",
        "agent_response": "I can help you upgrade! What's your order number so I can check your current seats and show you available upgrade options?",
        "tools_used": [],
        "expected_score": 0.85
    },
    {
        "name": "Price inquiry",
        "user_message": "How much are tickets?",
        "agent_response": "I'd be happy to help! Which event are you interested in? I can check pricing for specific games.",
        "tools_used": [],
        "expected_score": 0.75
    },
    {
        "name": "Complex request",
        "user_message": "I want to buy 4 tickets in section A, but if that's not available, section B works too",
        "agent_response": "I'll check availability for both sections. Let me search for 4 tickets in Section A first, and if those aren't available, I'll show you Section B options.",
        "tools_used": ["check_inventory"],
        "expected_score": 0.90
    },
    {
        "name": "Refund request",
        "user_message": "I need to cancel my order and get a refund",
        "agent_response": "I can help with that. What's your order number? I'll check our refund policy for your purchase.",
        "tools_used": ["get_order", "check_policy"],
        "expected_score": 0.85
    }
]


def run_example_evaluation():
    """Run example evaluation on test cases"""
    print("🧪 LLM-as-a-Judge Evaluation Demo")
    print("=" * 60)
    
    # Initialize judge
    try:
        judge = LLMJudge()
    except Exception as e:
        print(f"❌ Error initializing LLM Judge: {e}")
        print("\n💡 Make sure to set OPENAI_API_KEY environment variable:")
        print("   export OPENAI_API_KEY=your-api-key")
        return
    
    # Evaluate test cases
    print(f"\n📋 Evaluating {len(TICKETING_EVAL_CASES)} test cases...")
    print()
    
    results = []
    for i, test_case in enumerate(TICKETING_EVAL_CASES, 1):
        print(f"Test {i}/{len(TICKETING_EVAL_CASES)}: {test_case['name']}")
        
        result = judge.evaluate_response(
            user_message=test_case['user_message'],
            agent_response=test_case['agent_response'],
            tools_used=test_case.get('tools_used')
        )
        
        results.append(result)
        
        print(f"  Score: {result.overall_score:.2f} {'✅' if result.passed else '❌'}")
        print(f"  Feedback: {result.feedback[:100]}...")
        print()
    
    # Generate report
    print("=" * 60)
    print("📊 EVALUATION REPORT")
    print("=" * 60)
    
    report = judge.generate_eval_report(results)
    
    print(f"\n✅ Passed: {report['passed']}/{report['total_evaluated']} ({report['pass_rate']:.1%})")
    print(f"\n📈 Average Scores:")
    for dimension, score in report['average_scores'].items():
        print(f"   {dimension:20s}: {score:.2f}")
    
    print(f"\n⚠️  Weakest Dimension: {report['weakest_dimension']['name']} ({report['weakest_dimension']['score']:.2f})")
    print(f"\n💡 Recommendation: {report['recommendation']}")
    
    # Save detailed results
    output_file = "eval_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_cases": [asdict(r) for r in results],
            "summary": report
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    run_example_evaluation()
