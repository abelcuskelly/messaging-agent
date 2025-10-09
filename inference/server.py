import os
import json
import threading
from typing import List, Dict, Any, Optional

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from google.cloud import storage


app = FastAPI()


class PredictRequest(BaseModel):
    instances: List[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None


class ModelState:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.lock = threading.Lock()

    def ensure_loaded(self):
        if self.model is not None and self.tokenizer is not None:
            return
        with self.lock:
            if self.model is not None and self.tokenizer is not None:
                return
            model_dir = self._prepare_model_dir()
            self._load_from_dir(model_dir)

    @staticmethod
    def _prepare_model_dir() -> str:
        # Prefer AIP_STORAGE_URI (Vertex sets this to your artifact GCS URI)
        storage_uri = os.getenv("AIP_STORAGE_URI") or os.getenv("MODEL_GCS_URI")
        local_dir = os.getenv("MODEL_DIR", "/model")
        os.makedirs(local_dir, exist_ok=True)
        if storage_uri and storage_uri.startswith("gs://"):
            _download_gcs_dir(storage_uri, local_dir)
        return local_dir

    def _load_from_dir(self, model_dir: str) -> None:
        # Load fine-tuned or base model if artifacts missing
        model_name = os.getenv("HF_MODEL", "Qwen/Qwen3-4B-Instruct-2507")
        load_path = model_dir if os.path.exists(os.path.join(model_dir, "config.json")) else model_name
        self.model = AutoModelForCausalLM.from_pretrained(
            load_path,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True,
            attn_implementation=os.getenv("ATTN_IMPL", "flash_attention_2"),
        )
        self.tokenizer = AutoTokenizer.from_pretrained(load_path, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.model.config.eos_token_id


state = ModelState()


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(req: PredictRequest):
    state.ensure_loaded()

    params = req.parameters or {}
    max_new_tokens = int(params.get("max_new_tokens", 512))
    temperature = float(params.get("temperature", 0.7))
    top_p = float(params.get("top_p", 0.9))
    do_sample = bool(params.get("do_sample", True))

    predictions: List[Dict[str, Any]] = []

    for instance in req.instances:
        messages = instance.get("messages", [])
        # Build chat input
        text = state.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = state.tokenizer(text, return_tensors="pt").to(state.model.device)
        with torch.no_grad():
            output = state.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
            )
        completion = state.tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        predictions.append({"response": completion})

    return {"predictions": predictions}


def _download_gcs_dir(gs_uri: str, local_dir: str) -> None:
    # gs_uri like gs://bucket/path
    if not gs_uri.startswith("gs://"):
        return
    _, path = gs_uri.split("gs://", 1)
    bucket_name, *prefix_parts = path.split("/", 1)
    prefix = prefix_parts[0] if prefix_parts else ""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    for blob in client.list_blobs(bucket, prefix=prefix):
        rel = blob.name[len(prefix) :].lstrip("/") if prefix else blob.name
        if not rel:
            continue
        dest_path = os.path.join(local_dir, rel)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        blob.download_to_filename(dest_path)


