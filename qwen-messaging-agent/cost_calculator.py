class VertexAICostCalculator:
    """Calculate estimated costs for Vertex AI training and inference."""

    TRAINING_COSTS = {
        "n1-standard-8": 0.38,
        "n1-standard-16": 0.76,
        "NVIDIA_TESLA_T4": 0.35,
        "NVIDIA_TESLA_V100": 2.48,
        "NVIDIA_TESLA_A100": 3.67,
    }

    INFERENCE_COSTS = {
        "n1-standard-4": 0.19,
        "NVIDIA_TESLA_T4": 0.35,
    }

    STORAGE_COST_PER_GB = 0.020

    def calculate_training_cost(
        self,
        machine_type: str,
        accelerator_type: str,
        accelerator_count: int,
        training_hours: float,
    ):
        machine_cost = self.TRAINING_COSTS.get(machine_type, 0)
        gpu_cost = self.TRAINING_COSTS.get(accelerator_type, 0) * accelerator_count
        total_hourly = machine_cost + gpu_cost
        total_cost = total_hourly * training_hours
        return {
            "hourly_cost": total_hourly,
            "total_cost": total_cost,
            "breakdown": {
                "machine": machine_cost * training_hours,
                "gpu": gpu_cost * training_hours,
            },
        }

    def calculate_monthly_inference_cost(
        self,
        machine_type: str,
        accelerator_type: str,
        accelerator_count: int,
        requests_per_month: int,
        avg_tokens_per_request: int = 500,
        uptime_hours: int = 730,
    ):
        machine_cost = self.INFERENCE_COSTS.get(machine_type, 0)
        gpu_cost = self.INFERENCE_COSTS.get(accelerator_type, 0) * accelerator_count
        hosting_cost = (machine_cost + gpu_cost) * uptime_hours
        prediction_cost = (requests_per_month * avg_tokens_per_request) / 1_000_000 * 0.50
        return {
            "hosting_cost": hosting_cost,
            "prediction_cost": prediction_cost,
            "total_monthly": hosting_cost + prediction_cost,
        }

    def calculate_storage_cost(self, model_size_gb: float, months: int = 1):
        return model_size_gb * self.STORAGE_COST_PER_GB * months


