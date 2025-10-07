from kfp.v2 import dsl, compiler
from kfp.v2.dsl import component, Input, Output, Dataset, Model
from google.cloud import aiplatform


@component(base_image="python:3.10", packages_to_install=["google-cloud-storage"])
def prepare_data(bucket_name: str, output_dataset: Output[Dataset]):
    # Placeholder for data prep
    with open(output_dataset.path, "w", encoding="utf-8") as f:
        f.write("prepared-data-placeholder")


@component(
    base_image="us-docker.pkg.dev/vertex-ai/training/pytorch-gpu.2-1:latest",
    packages_to_install=["transformers", "peft", "trl", "datasets"],
)
def train_model(input_dataset: Input[Dataset], epochs: int, batch_size: int, output_model: Output[Model]):
    # Placeholder for training invocation
    with open(output_model.path, "w", encoding="utf-8") as f:
        f.write("trained-model-placeholder")


@component
def evaluate_model(model: Input[Model], test_dataset: Input[Dataset]) -> float:
    return 0.95


@component
def deploy_model(model: Input[Model], eval_score: float, threshold: float = 0.90):
    if eval_score >= threshold:
        pass


@dsl.pipeline(name="qwen-training-pipeline", description="End-to-end training pipeline")
def training_pipeline(bucket_name: str, epochs: int = 3, batch_size: int = 4):
    data_prep = prepare_data(bucket_name=bucket_name)
    training = train_model(input_dataset=data_prep.outputs["output_dataset"], epochs=epochs, batch_size=batch_size)
    evaluation = evaluate_model(model=training.outputs["output_model"], test_dataset=data_prep.outputs["output_dataset"]) 
    deploy_model(model=training.outputs["output_model"], eval_score=evaluation.output)


def compile_pipeline():
    compiler.Compiler().compile(pipeline_func=training_pipeline, package_path="qwen_pipeline.json")


