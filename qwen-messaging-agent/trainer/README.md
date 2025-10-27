# Model Training

Custom model training using LoRA fine-tuning on Google Cloud Vertex AI.

## Quick Start

```bash
# 1. Build and push training image
cd qwen-messaging-agent
python quick_start.py

# 2. Monitor training job
gcloud ai custom-jobs list \
  --project=your-project-id \
  --region=us-central1

# 3. After completion, deploy model
python deploy_to_vertex.py
```

## Training Process

### 1. Dataset Preparation
```bash
# Prepare your conversation dataset
python dataset.py \
  --input ./data/conversations.json \
  --output ./data/chat_dataset.json \
  --format alpaca  # or sharegpt, vicuna
```

### 2. Training Configuration
```python
# train.py configuration
--model_name Qwen/Qwen3-4B-Instruct-2507
--dataset_path ./data/chat_dataset.json
--output_dir ./outputs
--num_epochs 3
--batch_size 4
--gradient_accumulation_steps 8
--learning_rate 1e-4
--lora_r 16
--lora_alpha 32
--use_4bit True
```

### 3. Submit Training Job
```bash
python quick_start.py \
  --model_name Qwen/Qwen3-4B-Instruct-2507 \
  --dataset_path ./data/chat_dataset.json \
  --num_epochs 3
```

## Training Parameters

### LoRA Parameters
- **LoRA Rank (r)**: 16 (low-rank dimension)
- **LoRA Alpha**: 32 (scaling factor)
- **LoRA Dropout**: 0.1 (regularization)

### Optimization
- **Optimizer**: AdamW
- **Learning Rate**: 1e-4 (with warmup)
- **Weight Decay**: 0.01
- **Warmup Ratio**: 0.1

### Hardware
- **GPU**: T4/V100/A100 (as available)
- **Quantization**: 4-bit for memory efficiency
- **Batch Size**: 4 per device
- **Accumulation**: 8 steps

## Monitoring

### TensorBoard
```bash
tensorboard --logdir ./logs \
  --port 6006
```

### Cloud Console
```bash
# View logs
gcloud ai custom-jobs describe JOB_ID \
  --project=your-project-id \
  --region=us-central1
```

### Weights & Biases
```python
# Enable W&B tracking
WANDB_PROJECT=your-project WANDB_API_KEY=your-key python train.py
```

## Model Deployment

### After Training
```bash
# Deploy to Vertex AI Endpoint
python deploy_to_vertex.py \
  --model_path gs://bucket/models/merged \
  --endpoint_name qwen-messaging-endpoint
```

### Endpoint Configuration
```bash
# Create endpoint
gcloud ai endpoints create qwen-messaging-endpoint \
  --region=us-central1

# Deploy model
gcloud ai endpoints deploy-model ENDPOINT_ID \
  --model=MODEL_ID \
  --region=us-central1 \
  --traffic-percentage=100
```

## Dataset Formats

### Alpaca Format
```json
{
  "instruction": "Answer the question",
  "input": "What are Lakers tickets?",
  "output": "Lakers tickets are..."
}
```

### ShareGPT Format
```json
{
  "conversations": [
    {"from": "human", "value": "Hello"},
    {"from": "assistant", "value": "Hi! How can I help?"}
  ]
}
```

## Cost Estimation

See `cost_calculator.py` for detailed cost estimates:

```bash
python cost_calculator.py
```

Typical costs:
- **Training**: $50-200 (depending on GPU)
- **Inference**: $0.01-0.50 per 1M tokens
- **Storage**: $0.023 per GB/month

## Troubleshooting

### Common Issues
1. **Out of Memory**: Reduce batch_size or enable 4-bit
2. **Slow Training**: Use A100 GPU or increase batch size
3. **Poor Results**: Increase dataset size or epochs

### Debug Mode
```bash
python train.py --debug --num_epochs 1 --batch_size 1
```

## Documentation

- **[Training Script](./train.py)** - Main training logic
- **[Dataset Utils](./dataset.py)** - Dataset loading
- **[Cost Calculator](../cost_calculator.py)** - Cost estimation
