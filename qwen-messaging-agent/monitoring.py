from google.cloud import aiplatform


def enable_model_monitoring(endpoint_name: str) -> aiplatform.ModelDeploymentMonitoringJob:
    monitoring_job = aiplatform.ModelDeploymentMonitoringJob.create(
        display_name="qwen-monitoring",
        endpoint=endpoint_name,
        logging_sampling_strategy=aiplatform.RandomSampleConfig(sample_rate=0.5),
        schedule_config=aiplatform.MonitoringScheduleConfig(monitor_interval=3600),
    )
    return monitoring_job


