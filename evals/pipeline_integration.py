"""
Evaluation Pipeline Integration

Integrates evaluation into the training and deployment pipeline
for automated quality gates.

Features:
- Pre-deployment evaluation
- A/B testing evaluation
- Regression testing
- Continuous evaluation
"""

import os
import json
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from google.cloud import aiplatform, storage

from evals.eval_suite import EvaluationSuite

logger = logging.getLogger(__name__)


class PipelineEvaluator:
    """
    Evaluation component for ML pipelines
    
    Integrates with Vertex AI pipelines to automatically evaluate
    models before deployment.
    """
    
    def __init__(self,
                 project_id: str,
                 region: str,
                 bucket_name: str):
        self.project_id = project_id
        self.region = region
        self.bucket_name = bucket_name
        
        aiplatform.init(project=project_id, location=region)
        self.storage_client = storage.Client(project=project_id)
    
    def evaluate_endpoint(self,
                         endpoint_id: str,
                         test_cases: List[Dict[str, Any]],
                         min_score_threshold: float = 0.80,
                         min_pass_rate: float = 0.85) -> Dict[str, Any]:
        """
        Evaluate a deployed endpoint
        
        Args:
            endpoint_id: Vertex AI endpoint ID
            test_cases: List of test cases to run
            min_score_threshold: Minimum overall score to pass
            min_pass_rate: Minimum pass rate to deploy
        
        Returns:
            Evaluation results with deployment recommendation
        """
        logger.info(f"Evaluating endpoint: {endpoint_id}")
        
        # Initialize endpoint
        endpoint = aiplatform.Endpoint(
            f"projects/{self.project_id}/locations/{self.region}/endpoints/{endpoint_id}"
        )
        
        # Run test cases against endpoint
        test_results = []
        for test_case in test_cases:
            try:
                # Get prediction
                response = endpoint.predict(
                    instances=[{
                        "messages": [
                            {"role": "user", "content": test_case['user_message']}
                        ]
                    }]
                )
                
                # Add agent response to test case
                test_case['agent_response'] = response.predictions[0].get('response', '')
                test_results.append(test_case)
            
            except Exception as e:
                logger.error(f"Prediction failed for test case: {e}")
                test_case['agent_response'] = f"ERROR: {str(e)}"
                test_case['prediction_failed'] = True
                test_results.append(test_case)
        
        # Evaluate responses
        suite = EvaluationSuite()
        eval_results = suite.evaluate_batch(test_results)
        report = suite.generate_report(eval_results)
        
        # Deployment decision
        should_deploy = (
            report['summary']['pass_rate'] >= min_pass_rate and
            report['summary']['avg_overall_score'] >= min_score_threshold
        )
        
        report['deployment_decision'] = {
            "should_deploy": should_deploy,
            "pass_rate_threshold": min_pass_rate,
            "score_threshold": min_score_threshold,
            "actual_pass_rate": report['summary']['pass_rate'],
            "actual_score": report['summary']['avg_overall_score'],
            "reason": self._get_deployment_reason(
                should_deploy,
                report['summary']['pass_rate'],
                report['summary']['avg_overall_score'],
                min_pass_rate,
                min_score_threshold
            )
        }
        
        # Save to GCS
        self._save_to_gcs(report, endpoint_id)
        
        return report
    
    def _get_deployment_reason(self,
                              should_deploy: bool,
                              pass_rate: float,
                              avg_score: float,
                              min_pass_rate: float,
                              min_score: float) -> str:
        """Generate deployment decision reason"""
        
        if should_deploy:
            return f"✅ Model meets thresholds: {pass_rate:.1%} pass rate (>= {min_pass_rate:.1%}), {avg_score:.2f} avg score (>= {min_score:.2f})"
        else:
            reasons = []
            if pass_rate < min_pass_rate:
                reasons.append(f"Pass rate {pass_rate:.1%} below threshold {min_pass_rate:.1%}")
            if avg_score < min_score:
                reasons.append(f"Avg score {avg_score:.2f} below threshold {min_score:.2f}")
            
            return f"❌ Model does not meet thresholds: {'; '.join(reasons)}"
    
    def _save_to_gcs(self, report: Dict[str, Any], endpoint_id: str):
        """Save evaluation report to GCS"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        blob_name = f"evaluations/{endpoint_id}/{timestamp}_eval_report.json"
        
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(
            json.dumps(report, indent=2, default=str),
            content_type='application/json'
        )
        
        logger.info(f"Evaluation report saved to gs://{self.bucket_name}/{blob_name}")
        return f"gs://{self.bucket_name}/{blob_name}"
    
    def compare_endpoints(self,
                         endpoint_a_id: str,
                         endpoint_b_id: str,
                         test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare two endpoints (A/B testing)
        
        Args:
            endpoint_a_id: First endpoint to compare
            endpoint_b_id: Second endpoint to compare
            test_cases: Test cases to run on both
        
        Returns:
            Comparison results with winner recommendation
        """
        logger.info(f"Comparing endpoints: {endpoint_a_id} vs {endpoint_b_id}")
        
        # Evaluate both endpoints
        results_a = self.evaluate_endpoint(endpoint_a_id, test_cases.copy())
        results_b = self.evaluate_endpoint(endpoint_b_id, test_cases.copy())
        
        # Compare
        comparison = {
            "endpoint_a": {
                "endpoint_id": endpoint_a_id,
                "pass_rate": results_a['summary']['pass_rate'],
                "avg_score": results_a['summary']['avg_overall_score']
            },
            "endpoint_b": {
                "endpoint_id": endpoint_b_id,
                "pass_rate": results_b['summary']['pass_rate'],
                "avg_score": results_b['summary']['avg_overall_score']
            }
        }
        
        # Determine winner
        if results_a['summary']['avg_overall_score'] > results_b['summary']['avg_overall_score']:
            comparison['winner'] = 'endpoint_a'
            comparison['reason'] = f"Endpoint A scores higher: {results_a['summary']['avg_overall_score']:.2f} vs {results_b['summary']['avg_overall_score']:.2f}"
        elif results_b['summary']['avg_overall_score'] > results_a['summary']['avg_overall_score']:
            comparison['winner'] = 'endpoint_b'
            comparison['reason'] = f"Endpoint B scores higher: {results_b['summary']['avg_overall_score']:.2f} vs {results_a['summary']['avg_overall_score']:.2f}"
        else:
            comparison['winner'] = 'tie'
            comparison['reason'] = "Both endpoints perform equally"
        
        return comparison


def create_standard_test_cases() -> List[Dict[str, Any]]:
    """Create standard test cases for ticketing agent"""
    return [
        {
            "name": "Simple purchase",
            "user_message": "I need 2 tickets for tonight's game"
        },
        {
            "name": "Seat upgrade",
            "user_message": "Can I upgrade to better seats?"
        },
        {
            "name": "Price inquiry",
            "user_message": "How much are Section A tickets?"
        },
        {
            "name": "Event search",
            "user_message": "What Lakers games are coming up?"
        },
        {
            "name": "Refund request",
            "user_message": "I need to cancel my order"
        },
        {
            "name": "Complex request",
            "user_message": "I want 4 tickets in Section A or B, whichever is cheaper, for this weekend"
        },
        {
            "name": "Availability check",
            "user_message": "Are there any courtside seats available?"
        },
        {
            "name": "Group purchase",
            "user_message": "I need 10 tickets for a corporate event"
        },
        {
            "name": "Last minute",
            "user_message": "Do you have any tickets for tonight's game?"
        },
        {
            "name": "Budget constraint",
            "user_message": "I need tickets under $100 each"
        }
    ]


if __name__ == "__main__":
    print("📊 Pipeline Evaluation Demo")
    print("=" * 60)
    
    # Check for credentials
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set")
        print("\n💡 Set your API key:")
        print("   export OPENAI_API_KEY=your-api-key")
        exit(1)
    
    if not os.getenv('PROJECT_ID'):
        print("⚠️  PROJECT_ID not set, using demo mode")
        
        # Run demo without endpoint
        print("\n🧪 Running demo evaluation (no endpoint required)...")
        run_full_evaluation()
    else:
        # Run with actual endpoint
        evaluator = PipelineEvaluator(
            project_id=os.getenv('PROJECT_ID'),
            region=os.getenv('REGION', 'us-central1'),
            bucket_name=os.getenv('BUCKET_NAME')
        )
        
        endpoint_id = os.getenv('ENDPOINT_ID')
        if endpoint_id:
            print(f"\n🎯 Evaluating endpoint: {endpoint_id}")
            
            test_cases = create_standard_test_cases()
            results = evaluator.evaluate_endpoint(endpoint_id, test_cases)
            
            print(f"\n✅ Evaluation complete!")
            print(f"   Pass rate: {results['summary']['pass_rate']:.1%}")
            print(f"   Avg score: {results['summary']['avg_overall_score']:.2f}")
            print(f"\n💡 {results['deployment_decision']['reason']}")
        else:
            print("❌ ENDPOINT_ID not set")
