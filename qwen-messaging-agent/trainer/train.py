"""
Main training script for Qwen3 messaging agent
Runs on Vertex AI Custom Training
"""
import os
import argparse
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
from datasets import load_dataset
from google.cloud import storage
import wandb


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="Qwen/Qwen3-8B-Instruct")
    parser.add_argument("--output_dir", type=str, default="/tmp/output")
    parser.add_argument("--bucket_name", type=str, required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--dataset_name", type=str, default="OpenAssistant/oasst2")
    parser.add_argument("--wandb_project", type=str, default="qwen-messaging-agent")
    return parser.parse_args()


def setup_model_and_tokenizer(model_name):
    """Load model with 4-bit quantization."""
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
        attn_implementation="flash_attention_2",
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = model.config.eos_token_id

    return model, tokenizer


def prepare_dataset(dataset_name, tokenizer):
    """Load and format dataset for supervised fine-tuning."""
    dataset = load_dataset(dataset_name, split="train[:10000]")  # Sample for demo

    def format_chat(example):
        # Convert to Qwen3 chat format
        if "messages" in example:
            messages = example["messages"]
        else:
            messages = [
                {"role": "user", "content": example.get("prompt", "")},
                {"role": "assistant", "content": example.get("response", "")},
            ]

        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    formatted_dataset = dataset.map(
        format_chat,
        remove_columns=dataset.column_names,
    )

    split_dataset = formatted_dataset.train_test_split(test_size=0.05, seed=42)
    return split_dataset["train"], split_dataset["test"]


def setup_lora_config():
    """Configure LoRA for parameter-efficient fine-tuning."""
    return LoraConfig(
        r=64,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )


def upload_to_gcs(local_path, bucket_name, gcs_path):
    """Upload trained model directory to Cloud Storage recursively."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for root, _dirs, files in os.walk(local_path):
        for file in files:
            local_file = os.path.join(root, file)
            relative_path = os.path.relpath(local_file, local_path)
            blob_path = os.path.join(gcs_path, relative_path)

            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_file)
            print(f"Uploaded {local_file} to gs://{bucket_name}/{blob_path}")


def main():
    args = parse_args()

    # Initialize Weights & Biases
    wandb.init(project=args.wandb_project, config=vars(args))

    print("Loading model and tokenizer...")
    model, tokenizer = setup_model_and_tokenizer(args.model_name)

    print("Preparing dataset...")
    train_dataset, eval_dataset = prepare_dataset(args.dataset_name, tokenizer)

    print("Setting up LoRA...")
    lora_config = setup_lora_config()
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        learning_rate=args.learning_rate,
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
        report_to="wandb",
        load_best_model_at_end=True,
    )

    # Data collator - focus loss on assistant completions
    response_template = "<|im_start|>assistant"
    collator = DataCollatorForCompletionOnlyLM(
        response_template=response_template,
        tokenizer=tokenizer,
    )

    # Initialize trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=collator,
        max_seq_length=2048,
        packing=False,
        dataset_text_field="text",
    )

    print("Starting training...")
    trainer.train()

    print("Saving final model...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # Save merged model for standalone inference
    merged_model = model.merge_and_unload()
    merged_output = os.path.join(args.output_dir, "merged")
    os.makedirs(merged_output, exist_ok=True)
    merged_model.save_pretrained(merged_output)
    tokenizer.save_pretrained(merged_output)

    # Upload to GCS
    print("Uploading to Cloud Storage...")
    upload_to_gcs(args.output_dir, args.bucket_name, "qwen-messaging-agent/models")

    print("Training complete!")
    wandb.finish()


if __name__ == "__main__":
    main()


