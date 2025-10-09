from google.cloud import aiplatform
import os
from typing import Optional


def enable_model_monitoring(
    endpoint_name: str,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    sample_rate: float = 0.1,
    monitor_interval: int = 3600
) -> aiplatform.ModelDeploymentMonitoringJob:
    """Enable Vertex AI Model Monitoring for an endpoint.
    
    Args:
        endpoint_name: Full endpoint resource name
        project_id: GCP project ID (defaults to env var)
        region: GCP region (defaults to env var)
        sample_rate: Fraction of requests to sample (0.0-1.0)
        monitor_interval: Monitoring check interval in seconds
    
    Returns:
        ModelDeploymentMonitoringJob instance
    """
    if project_id:
        aiplatform.init(project=project_id, location=region or "us-central1")
    
    # Create monitoring job with drift detection
    monitoring_job = aiplatform.ModelDeploymentMonitoringJob.create(
        display_name="qwen-messaging-agent-monitoring",
        endpoint=endpoint_name,
        logging_sampling_strategy=aiplatform.RandomSampleConfig(sample_rate=sample_rate),
        schedule_config=aiplatform.MonitoringScheduleConfig(monitor_interval=monitor_interval),
        # Enable prediction drift detection
        model_monitoring_objective_configs=[
            aiplatform.ModelMonitoringObjectiveConfig(
                training_dataset=aiplatform.ModelMonitoringInput(
                    gcs_source=aiplatform.GcsSource(
                        uris=[os.getenv("TRAINING_DATA_URI", "gs://your-bucket/training-data")]
                    )
                ),
                training_prediction_skew_detection_config=aiplatform.SamplingStrategy(
                    random_sample_config=aiplatform.RandomSampleConfig(sample_rate=0.1)
                ),
                prediction_drift_detection_config=aiplatform.SamplingStrategy(
                    random_sample_config=aiplatform.RandomSampleConfig(sample_rate=0.1)
                )
            )
        ],
        # Alert configuration
        notification_channels=[
            # Add your notification channel IDs here
            # "projects/PROJECT_ID/notificationChannels/CHANNEL_ID"
        ]
    )
    
    print(f"Model monitoring enabled: {monitoring_job.resource_name}")
    return monitoring_job


def create_monitoring_dashboard(project_id: str, endpoint_name: str) -> str:
    """Create a Cloud Monitoring dashboard for model monitoring.
    
    Returns:
        Dashboard URL
    """
    from google.cloud import monitoring_v3
    
    client = monitoring_v3.DashboardServiceClient()
    project_path = f"projects/{project_id}"
    
    # Extract endpoint ID from endpoint name
    endpoint_id = endpoint_name.split("/")[-1]
    
    dashboard_config = {
        "displayName": "Qwen Messaging Agent Monitoring",
        "mosaicLayout": {
            "tiles": [
                {
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Prediction Requests",
                        "xyChart": {
                            "dataSets": [
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": f'resource.type="aiplatform.googleapis.com/Endpoint" AND resource.labels.endpoint_id="{endpoint_id}"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_RATE"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                },
                {
                    "width": 6,
                    "height": 4,
                    "xPos": 6,
                    "widget": {
                        "title": "Prediction Latency",
                        "xyChart": {
                            "dataSets": [
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": f'resource.type="aiplatform.googleapis.com/Endpoint" AND resource.labels.endpoint_id="{endpoint_id}"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_MEAN"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }
    }
    
    dashboard = client.create_dashboard(
        parent=project_path,
        dashboard=dashboard_config
    )
    
    return f"https://console.cloud.google.com/monitoring/dashboards/custom/{dashboard.name.split('/')[-1]}?project={project_id}"
