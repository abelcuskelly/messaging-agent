# Evaluation System - LLM-as-a-Judge + Domain Checks

Comprehensive evaluation system combining OpenAI GPT-4 evaluation with domain-specific rule-based checks.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r evals/requirements.txt
```

### 2. Set API Key
```bash
export OPENAI_API_KEY=your-openai-api-key
```

### 3. Run Evaluation
```bash
# Run full evaluation suite
cd evals
python eval_suite.py
```

This will:
1. Evaluate 9 standard ticketing test cases
2. Run both LLM judge and domain checks
3. Generate comprehensive report
4. Save detailed results to JSON
5. Provide deployment recommendation

## 🎯 Evaluation Dimensions

### LLM-as-a-Judge Evaluates:
1. **Helpfulness** (0.0-1.0) - Does it help the customer?
2. **Accuracy** (0.0-1.0) - Is information correct?
3. **Appropriateness** (0.0-1.0) - Professional tone?
4. **Tool Usage** (0.0-1.0) - Right tools used?
5. **Conversation Flow** (0.0-1.0) - Natural progression?
6. **Domain Expertise** (0.0-1.0) - Ticketing knowledge?

### Domain Checks Validate:
1. **Price Accuracy** - Math, formatting, totals
2. **Inventory Validation** - Availability claims
3. **Order Flow** - Correct step sequence
4. **Policy Compliance** - Refund, purchase policies
5. **Tool Usage** - Appropriate tool selection

## 📊 Evaluation Workflow

```
Test Case → Agent Response → Parallel Evaluation
                              ├─ LLM Judge (GPT-4)
                              │  └─ 6 dimension scores
                              └─ Domain Checks (Rules)
                                 └─ 5 category checks
                              
Combined Result → Overall Score → Pass/Fail → Recommendation
```

## 💡 Use Cases

### 1. Pre-Deployment Evaluation
```python
from evals import PipelineEvaluator

evaluator = PipelineEvaluator(project_id, region, bucket_name)

# Evaluate before deploying
report = evaluator.evaluate_endpoint(
    endpoint_id="new-model-endpoint",
    test_cases=standard_test_cases,
    min_score_threshold=0.85,
    min_pass_rate=0.90
)

if report['deployment_decision']['should_deploy']:
    # Deploy to production
    deploy_model()
else:
    # More training needed
    print(report['deployment_decision']['reason'])
```

### 2. A/B Testing
```python
# Compare two model versions
comparison = evaluator.compare_endpoints(
    endpoint_a_id="current-model",
    endpoint_b_id="new-model",
    test_cases=test_cases
)

print(f"Winner: {comparison['winner']}")
print(f"Reason: {comparison['reason']}")
```

### 3. Regression Testing
```python
# Run after each training iteration
suite = EvaluationSuite()
results = suite.evaluate_batch(regression_test_cases)

# Check if performance degraded
if results['summary']['avg_overall_score'] < previous_score:
    alert("Model performance degraded!")
```

### 4. Continuous Evaluation
```python
# Evaluate production responses daily
from production import get_sample_conversations

conversations = get_sample_conversations(days=1, sample_size=100)
results = suite.evaluate_batch(conversations)

# Track over time
log_metrics({
    "date": today,
    "pass_rate": results['summary']['pass_rate'],
    "avg_score": results['summary']['avg_overall_score']
})
```

## 📈 Performance

| Evaluation Type | Time per Test | Cost per Test |
|----------------|---------------|---------------|
| Domain Checks | ~5ms | $0.00 |
| LLM Judge (GPT-4) | ~500ms | ~$0.01 |
| Combined | ~505ms | ~$0.01 |
| Batch (10 tests) | ~5s | ~$0.10 |

**Optimization**: Run domain checks first (free), only use LLM judge for edge cases or detailed evaluation.

## 🔧 Configuration

### Environment Variables

```bash
# LLM Judge Configuration
export OPENAI_API_KEY=your-openai-key
export EVAL_MODEL=gpt-4-turbo-preview  # or gpt-4, gpt-3.5-turbo
export EVAL_PROVIDER=openai  # or 'vertexai'

# Pipeline Integration
export PROJECT_ID=your-gcp-project
export REGION=us-central1
export BUCKET_NAME=your-bucket
export ENDPOINT_ID=your-endpoint-id

# Thresholds
export MIN_EVAL_SCORE=0.80
export MIN_PASS_RATE=0.85
```

### Evaluation Thresholds

Recommended thresholds based on deployment type:

| Deployment | Min Score | Min Pass Rate | Use Case |
|------------|-----------|---------------|----------|
| Production | 0.90 | 0.95 | Customer-facing |
| Staging | 0.80 | 0.85 | Internal testing |
| Development | 0.70 | 0.75 | Experimental |

## 🧪 Example Output

```json
{
  "summary": {
    "total_cases": 10,
    "passed": 9,
    "failed": 1,
    "pass_rate": 0.90,
    "avg_overall_score": 0.87
  },
  "llm_judge_stats": {
    "avg_helpfulness": 0.92,
    "avg_accuracy": 0.88,
    "avg_appropriateness": 0.90,
    "avg_tool_usage": 0.85,
    "avg_conversation_flow": 0.89,
    "avg_domain_expertise": 0.84
  },
  "domain_check_stats": {
    "total_checks": 45,
    "checks_passed": 42,
    "checks_failed": 3,
    "check_pass_rate": 0.93
  },
  "recommendation": "✅ READY FOR PRODUCTION - Good performance, monitor tool usage"
}
```

## 🎯 Best Practices

### 1. Layered Evaluation
```python
# Fast domain checks first
domain_result = domain_evaluator.evaluate(msg, response)

if not domain_result['passed']:
    return "FAIL - Domain checks"

# Then expensive LLM evaluation
llm_result = llm_judge.evaluate_response(msg, response)
```

### 2. Test Case Coverage
Ensure test cases cover:
- ✅ Happy path (normal purchases)
- ✅ Edge cases (sold out, refunds)
- ✅ Error scenarios (invalid input)
- ✅ Complex workflows (multi-step)

### 3. Continuous Monitoring
```python
# Evaluate sample of production traffic daily
sample = get_production_sample(size=100)
results = suite.evaluate_batch(sample)

# Alert if scores drop
if results['avg_score'] < baseline - 0.05:
    send_alert("Model performance degraded")
```

## 🚨 Troubleshooting

### OpenAI API Errors
**Issue**: "Authentication failed"
**Solution**: Check OPENAI_API_KEY is set correctly

**Issue**: "Rate limit exceeded"
**Solution**: Reduce batch size or add delay between evaluations

### Low Scores
**Issue**: "Low helpfulness scores"
**Solution**: Improve prompt engineering, add more few-shot examples

**Issue**: "Domain checks failing"
**Solution**: Fix specific issues (price math, inventory logic)

## 📚 Resources

- [OpenAI API Docs](https://platform.openai.com/docs)
- [LLM-as-a-Judge Paper](https://arxiv.org/abs/2306.05685)
- [Vertex AI Evaluation](https://cloud.google.com/vertex-ai/docs/generative-ai/models/evaluate-models)

## 🤝 Contributing

To add new evaluation dimensions:

1. Add to LLM judge prompt in `llm_judge.py`
2. Create new checker in `domain_specific.py`
3. Update `eval_suite.py` to include new checker
4. Add test cases
5. Update documentation

## ✅ Checklist

Before using in production:
- [ ] Set OPENAI_API_KEY
- [ ] Test with sample cases
- [ ] Define pass/fail thresholds
- [ ] Set up automated pipeline
- [ ] Configure alerts for failures
- [ ] Document custom test cases
- [ ] Train team on interpreting results
