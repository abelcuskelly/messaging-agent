from kfp.v2 import dsl, compiler
from kfp.v2.dsl import component, Input, Output, Dataset, Model, Metrics
from google.cloud import aiplatform
import os
import json
from typing import Dict, Any


@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-storage", "datasets", "transformers"]
)
def prepare_data(
    bucket_name: str,
    dataset_name: str,
    output_dataset: Output[Dataset],
    output_metrics: Output[Metrics]
) -> Dict[str, Any]:
    """Prepare and validate training data."""
    from google.cloud import storage
    from datasets import load_dataset
    import json
    
    # Load dataset
    dataset = load_dataset(dataset_name, split="train[:10000]")
    
    # Basic data validation
    total_samples = len(dataset)
    valid_samples = 0
    
    for example in dataset:
        if "messages" in example or ("prompt" in example and "response" in example):
            valid_samples += 1
    
    validation_rate = valid_samples / total_samples if total_samples > 0 else 0
    
    # Save prepared data info
    data_info = {
        "total_samples": total_samples,
        "valid_samples": valid_samples,
        "validation_rate": validation_rate,
        "dataset_name": dataset_name
    }
    
    with open(output_dataset.path, "w") as f:
        json.dump(data_info, f)
    
    # Log metrics
    metrics = {
        "total_samples": total_samples,
        "valid_samples": valid_samples,
        "validation_rate": validation_rate
    }
    
    with open(output_metrics.path, "w") as f:
        json.dump(metrics, f)
    
    return data_info


@component(
    base_image="us-docker.pkg.dev/vertex-ai/training/pytorch-gpu.2-1:latest",
    packages_to_install=["transformers", "peft", "trl", "datasets", "wandb", "google-cloud-storage"]
)
def train_model(
    input_dataset: Input[Dataset],
    model_name: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    bucket_name: str,
    output_model: Output[Model],
    output_metrics: Output[Metrics]
) -> Dict[str, Any]:
    """Train the Qwen model with LoRA."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
    from datasets import load_dataset
    from google.cloud import storage
    import json
    import os
    
    # Load model with 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load and prepare dataset
    dataset = load_dataset("OpenAssistant/oasst2", split="train[:5000]")
    
    def format_chat(example):
        if "messages" in example:
            messages = example["messages"]
        else:
            messages = [
                {"role": "user", "content": example.get("prompt", "")},
                {"role": "assistant", "content": example.get("response", "")},
            ]
        
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        return {"text": text}
    
    formatted_dataset = dataset.map(format_chat, remove_columns=dataset.column_names)
    split_dataset = formatted_dataset.train_test_split(test_size=0.05, seed=42)
    
    # Setup LoRA
    lora_config = LoraConfig(
        r=64,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="/tmp/output",
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.01,
        fp16=False,
        bf16=True,
        max_grad_norm=0.3,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
        evaluation_strategy="steps",
        eval_steps=100,
        load_best_model_at_end=True,
    )
    
    # Data collator
    response_template = "<|im_start|>assistant"
    collator = DataCollatorForCompletionOnlyLM(
        response_template=response_template, tokenizer=tokenizer
    )
    
    # Initialize trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=split_dataset["train"],
        eval_dataset=split_dataset["test"],
        tokenizer=tokenizer,
        data_collator=collator,
        max_seq_length=2048,
        packing=False,
        dataset_text_field="text",
    )
    
    # Train model
    trainer.train()
    
    # Save model
    trainer.save_model("/tmp/output")
    tokenizer.save_pretrained("/tmp/output")
    
    # Save merged model
    merged_model = model.merge_and_unload()
    merged_output = "/tmp/output/merged"
    os.makedirs(merged_output, exist_ok=True)
    merged_model.save_pretrained(merged_output)
    tokenizer.save_pretrained(merged_output)
    
    # Upload to GCS
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    for root, dirs, files in os.walk("/tmp/output"):
        for file in files:
            local_file = os.path.join(root, file)
            relative_path = os.path.relpath(local_file, "/tmp/output")
            blob_path = f"qwen-messaging-agent/models/{relative_path}"
            
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_file)
    
    # Training metrics
    training_metrics = {
        "final_train_loss": trainer.state.log_history[-1].get("train_loss", 0),
        "final_eval_loss": trainer.state.log_history[-1].get("eval_loss", 0),
        "epochs_completed": epochs,
        "model_name": model_name
    }
    
    with open(output_metrics.path, "w") as f:
        json.dump(training_metrics, f)
    
    # Save model info
    model_info = {
        "model_path": f"gs://{bucket_name}/qwen-messaging-agent/models/merged",
        "training_metrics": training_metrics
    }
    
    with open(output_model.path, "w") as f:
        json.dump(model_info, f)
    
    return model_info


@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-storage", "transformers", "datasets"]
)
def evaluate_model(
    model: Input[Model],
    test_dataset: Input[Dataset],
    output_metrics: Output[Metrics]
) -> float:
    """Evaluate the trained model."""
    import json
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from datasets import load_dataset
    from google.cloud import storage
    import os
    
    # Load model info
    with open(model.path, "r") as f:
        model_info = json.load(f)
    
    model_path = model_info["model_path"]
    
    # Download model from GCS
    local_model_path = "/tmp/eval_model"
    os.makedirs(local_model_path, exist_ok=True)
    
    client = storage.Client()
    bucket_name = model_path.split("/")[2]
    prefix = "/".join(model_path.split("/")[3:])
    bucket = client.bucket(bucket_name)
    
    for blob in bucket.list_blobs(prefix=prefix):
        local_file = os.path.join(local_model_path, blob.name[len(prefix):].lstrip("/"))
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
        blob.download_to_filename(local_file)
    
    # Load model and tokenizer
    model_obj = AutoModelForCausalLM.from_pretrained(
        local_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(local_model_path)
    
    # Load test dataset
    test_data = load_dataset("OpenAssistant/oasst2", split="test[:100]")
    
    # Simple evaluation: generate responses and check length
    total_length = 0
    valid_responses = 0
    
    for example in test_data:
        messages = example.get("messages", [])
        if not messages:
            continue
            
        # Format input
        text = tokenizer.apply_chat_template(
            messages[:-1], tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model_obj.device)
        
        # Generate response
        with torch.no_grad():
            outputs = model_obj.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True
            )
        
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True
        )
        
        if len(response.strip()) > 10:  # Valid response
            valid_responses += 1
            total_length += len(response)
    
    # Calculate metrics
    avg_response_length = total_length / valid_responses if valid_responses > 0 else 0
    response_rate = valid_responses / len(test_data) if test_data else 0
    
    # Composite score (simplified)
    eval_score = (response_rate * 0.7) + (min(avg_response_length / 100, 1.0) * 0.3)
    
    eval_metrics = {
        "eval_score": eval_score,
        "response_rate": response_rate,
        "avg_response_length": avg_response_length,
        "valid_responses": valid_responses,
        "total_samples": len(test_data)
    }
    
    with open(output_metrics.path, "w") as f:
        json.dump(eval_metrics, f)
    
    return eval_score


@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"]
)
def deploy_model(
    model: Input[Model],
    eval_score: float,
    threshold: float,
    project_id: str,
    region: str,
    bucket_name: str
) -> str:
    """Deploy model if it meets the quality threshold."""
    from google.cloud import aiplatform
    import json
    
    if eval_score < threshold:
        print(f"Model score {eval_score:.3f} below threshold {threshold}, skipping deployment")
        return "not_deployed"
    
    # Load model info
    with open(model.path, "r") as f:
        model_info = json.load(f)
    
    model_path = model_info["model_path"]
    
    # Initialize Vertex AI
    aiplatform.init(project=project_id, location=region)
    
    # Upload model to Vertex AI
    uploaded_model = aiplatform.Model.upload(
        display_name="qwen-messaging-agent-pipeline",
        artifact_uri=model_path,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/pytorch-gpu.2-1:latest",
    )
    
    # Create endpoint
    endpoint = aiplatform.Endpoint.create(
        display_name="qwen-messaging-agent-pipeline-endpoint",
    )
    
    # Deploy model
    endpoint.deploy(
        model=uploaded_model,
        deployed_model_display_name="qwen-pipeline-v1",
        machine_type="n1-standard-4",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        min_replica_count=1,
        max_replica_count=3,
        traffic_split={"0": 100},
    )
    
    print(f"Model deployed to endpoint: {endpoint.resource_name}")
    return endpoint.resource_name


@dsl.pipeline(
    name="qwen-messaging-agent-pipeline",
    description="End-to-end pipeline: data prep → train → eval → conditional deploy"
)
def qwen_training_pipeline(
    bucket_name: str,
    dataset_name: str = "OpenAssistant/oasst2",
    model_name: str = "Qwen/Qwen3-4B-Instruct-2507",
    epochs: int = 2,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    eval_threshold: float = 0.7,
    project_id: str = "your-project-id",
    region: str = "us-central1"
):
    """Complete training pipeline with conditional deployment."""
    
    # Step 1: Prepare data
    data_prep = prepare_data(
        bucket_name=bucket_name,
        dataset_name=dataset_name
    )
    
    # Step 2: Train model
    training = train_model(
        input_dataset=data_prep.outputs["output_dataset"],
        model_name=model_name,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        bucket_name=bucket_name
    )
    
    # Step 3: Evaluate model
    evaluation = evaluate_model(
        model=training.outputs["output_model"],
        test_dataset=data_prep.outputs["output_dataset"]
    )
    
    # Step 4: Conditional deployment
    deployment = deploy_model(
        model=training.outputs["output_model"],
        eval_score=evaluation.output,
        threshold=eval_threshold,
        project_id=project_id,
        region=region,
        bucket_name=bucket_name
    )


def compile_pipeline():
    """Compile the pipeline to JSON."""
    compiler.Compiler().compile(
        pipeline_func=qwen_training_pipeline,
        package_path="qwen_pipeline.json"
    )
    print("Pipeline compiled to qwen_pipeline.json")


def run_pipeline(
    project_id: str,
    region: str,
    bucket_name: str,
    pipeline_root: str = None
):
    """Run the compiled pipeline."""
    if pipeline_root is None:
        pipeline_root = f"gs://{bucket_name}/pipeline-runs"
    
    aiplatform.init(project=project_id, location=region)
    
    job = aiplatform.PipelineJob(
        display_name="qwen-messaging-agent-pipeline-run",
        template_path="qwen_pipeline.json",
        pipeline_root=pipeline_root,
        parameter_values={
            "bucket_name": bucket_name,
            "dataset_name": "OpenAssistant/oasst2",
            "model_name": "Qwen/Qwen3-4B-Instruct-2507",
            "epochs": 2,
            "batch_size": 4,
            "learning_rate": 2e-4,
            "eval_threshold": 0.7,
            "project_id": project_id,
            "region": region
        }
    )
    
    job.submit()
    print(f"Pipeline job submitted: {job.resource_name}")
    return job


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "compile":
        compile_pipeline()
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        if len(sys.argv) < 4:
            print("Usage: python pipeline.py run <project_id> <region> <bucket_name>")
            sys.exit(1)
        
        run_pipeline(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Usage: python pipeline.py [compile|run]")
        sys.exit(1)
