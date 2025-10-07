from google.cloud import bigquery
import json
import datetime


class ConversationLogger:
    def __init__(self, project_id: str, dataset_id: str = "messaging_logs"):
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id
        self.table_id = "conversations"

    def log_interaction(self, conversation_id: str, user_message: str, agent_response: str, metadata: dict):
        rows_to_insert = [
            {
                "conversation_id": conversation_id,
                "user_message": user_message,
                "agent_response": agent_response,
                "metadata": json.dumps(metadata),
                "timestamp": datetime.datetime.now().isoformat(),
            }
        ]
        table_ref = f"{self.client.project}.{self.dataset_id}.{self.table_id}"
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            print(f"Errors inserting rows: {errors}")


