from google.cloud import bigquery
import json
import datetime
import os
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


class ConversationLogger:
    def __init__(self, project_id: Optional[str] = None, dataset_id: str = "messaging_logs"):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        if not self.project_id:
            raise ValueError("PROJECT_ID must be set")
        
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_id = dataset_id
        self.table_id = "conversations"
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create the conversations table if it doesn't exist."""
        dataset_ref = self.client.dataset(self.dataset_id)
        table_ref = dataset_ref.table(self.table_id)
        
        try:
            self.client.get_table(table_ref)
        except Exception:
            # Table doesn't exist, create it
            schema = [
                bigquery.SchemaField("conversation_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_message", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("agent_response", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("request_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("duration_ms", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("message_length", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("response_length", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            ]
            
            table = bigquery.Table(table_ref, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            
            self.client.create_table(table)
            logger.info("Created BigQuery table", table=f"{self.dataset_id}.{self.table_id}")

    def log_interaction(
        self,
        conversation_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        status: str = "success"
    ):
        """Log a conversation interaction to BigQuery."""
        try:
            rows_to_insert = [
                {
                    "conversation_id": conversation_id,
                    "user_message": user_message,
                    "agent_response": agent_response,
                    "metadata": json.dumps(metadata or {}),
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "message_length": len(user_message),
                    "response_length": len(agent_response),
                    "status": status,
                }
            ]
            
            table_ref = f"{self.client.project}.{self.dataset_id}.{self.table_id}"
            errors = self.client.insert_rows_json(table_ref, rows_to_insert)
            
            if errors:
                logger.error("BigQuery insert errors", errors=errors)
            else:
                logger.info("Logged conversation to BigQuery", conversation_id=conversation_id)
                
        except Exception as e:
            logger.error("Failed to log conversation", error=str(e))

    def log_error(
        self,
        conversation_id: str,
        user_message: str,
        error_detail: str,
        request_id: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """Log a failed conversation interaction."""
        self.log_interaction(
            conversation_id=conversation_id,
            user_message=user_message,
            agent_response="",
            metadata={"error": error_detail},
            request_id=request_id,
            duration_ms=duration_ms,
            status="error"
        )

    def get_conversation_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get conversation statistics for the last N days."""
        query = f"""
        SELECT 
            COUNT(*) as total_conversations,
            COUNTIF(status = 'success') as successful_conversations,
            COUNTIF(status = 'error') as failed_conversations,
            AVG(duration_ms) as avg_duration_ms,
            AVG(message_length) as avg_message_length,
            AVG(response_length) as avg_response_length
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        """
        
        try:
            results = self.client.query(query).result()
            row = next(results)
            return {
                "total_conversations": row.total_conversations,
                "successful_conversations": row.successful_conversations,
                "failed_conversations": row.failed_conversations,
                "success_rate": row.successful_conversations / row.total_conversations if row.total_conversations > 0 else 0,
                "avg_duration_ms": row.avg_duration_ms,
                "avg_message_length": row.avg_message_length,
                "avg_response_length": row.avg_response_length,
            }
        except Exception as e:
            logger.error("Failed to get conversation stats", error=str(e))
            return {}
