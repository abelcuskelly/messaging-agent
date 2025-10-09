"""
Knowledge Base Setup for Ticket Information
This script helps you create and populate a knowledge base for your RAG system
"""

import os
import json
import csv
from typing import List, Dict, Any
from google.cloud import aiplatform_v1
from vertexai.language_models import TextEmbeddingModel
import structlog

logger = structlog.get_logger()


class KnowledgeBaseBuilder:
    """Build and manage knowledge base for ticket information."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create text embedding using Vertex AI."""
        try:
            embeddings = self.embedding_model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            logger.error("Failed to create embedding", error=str(e))
            raise
    
    def process_ticket_data(self, data_source: str) -> List[Dict[str, Any]]:
        """Process ticket data from various sources."""
        documents = []
        
        if data_source.endswith('.json'):
            documents = self._process_json_data(data_source)
        elif data_source.endswith('.csv'):
            documents = self._process_csv_data(data_source)
        elif data_source.endswith('.txt'):
            documents = self._process_text_data(data_source)
        else:
            raise ValueError(f"Unsupported file format: {data_source}")
        
        return documents
    
    def _process_json_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Process JSON ticket data."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        documents = []
        
        # Handle different JSON structures
        if isinstance(data, list):
            for i, item in enumerate(data):
                doc = self._create_document_from_dict(item, f"json_item_{i}")
                documents.append(doc)
        elif isinstance(data, dict):
            # Handle nested structures
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    doc = self._create_document_from_dict(value, f"json_{key}")
                    documents.append(doc)
                else:
                    doc = {
                        "id": f"json_{key}",
                        "content": f"{key}: {value}",
                        "source": "ticket_data",
                        "category": "general"
                    }
                    documents.append(doc)
        
        return documents
    
    def _process_csv_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Process CSV ticket data."""
        documents = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Create content from all columns
                content_parts = []
                for key, value in row.items():
                    if value and str(value).strip():
                        content_parts.append(f"{key}: {value}")
                
                content = " | ".join(content_parts)
                
                doc = {
                    "id": f"csv_row_{i}",
                    "content": content,
                    "source": "ticket_data",
                    "category": "ticket_info"
                }
                documents.append(doc)
        
        return documents
    
    def _process_text_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Process plain text ticket data."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Split into chunks (you can customize this logic)
        chunks = self._split_text_into_chunks(content, chunk_size=500)
        
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "id": f"text_chunk_{i}",
                "content": chunk,
                "source": "ticket_data",
                "category": "general"
            }
            documents.append(doc)
        
        return documents
    
    def _create_document_from_dict(self, data: Dict[str, Any], base_id: str) -> Dict[str, Any]:
        """Create a document from a dictionary."""
        content_parts = []
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                content_parts.append(f"{key}: {json.dumps(value)}")
            else:
                content_parts.append(f"{key}: {value}")
        
        content = " | ".join(content_parts)
        
        return {
            "id": base_id,
            "content": content,
            "source": "ticket_data",
            "category": "ticket_info"
        }
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into manageable chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def create_sample_ticket_data(self) -> List[Dict[str, Any]]:
        """Create sample ticket data for testing."""
        return [
            {
                "id": "lakers-pricing-1",
                "content": "Lakers vs Warriors - March 15, 2024 - Crypto.com Arena. Lower bowl seats: $150-300, Upper bowl: $50-120, Courtside: $800-2000. Game time: 7:30 PM PST.",
                "source": "ticket_pricing",
                "category": "pricing"
            },
            {
                "id": "lakers-pricing-2", 
                "content": "Lakers vs Celtics - March 20, 2024 - Crypto.com Arena. Lower bowl seats: $180-350, Upper bowl: $60-140, Courtside: $900-2200. Game time: 7:00 PM PST.",
                "source": "ticket_pricing",
                "category": "pricing"
            },
            {
                "id": "upgrade-policy-1",
                "content": "Seat upgrades available up to 2 hours before game time. Upgrade cost is the difference between current seat price and new seat price plus $25 processing fee. Upgrades subject to availability.",
                "source": "upgrade_policy",
                "category": "upgrades"
            },
            {
                "id": "refund-policy-1",
                "content": "Full refunds available up to 48 hours before game time. Partial refunds (75%) available 24-48 hours before. No refunds within 24 hours of game time. Exchanges may be available for a $15 fee.",
                "source": "refund_policy",
                "category": "refunds"
            },
            {
                "id": "parking-info-1",
                "content": "Crypto.com Arena parking: General parking $25-40, Premium parking $50-75, Valet parking $60-80. Parking opens 2 hours before game time. Limited street parking available.",
                "source": "parking_info",
                "category": "parking"
            },
            {
                "id": "concessions-1",
                "content": "Arena concessions: Beer $12-15, Soft drinks $6-8, Hot dogs $8-12, Pizza $15-20, Nachos $10-14. Premium dining options available in club sections.",
                "source": "concessions",
                "category": "food"
            },
            {
                "id": "seating-chart-1",
                "content": "Crypto.com Arena seating: Lower bowl sections 101-130 (closest to court), Upper bowl sections 301-330 (higher up), Club sections 200s (premium amenities), Courtside rows A-F (VIP experience).",
                "source": "seating_info",
                "category": "seating"
            },
            {
                "id": "team-stats-1",
                "content": "Lakers 2023-24 season: 45-25 record, 3rd in Western Conference. LeBron James averaging 25.2 points, Anthony Davis 24.8 points. Home record: 28-8, Away record: 17-17.",
                "source": "team_stats",
                "category": "statistics"
            }
        ]
    
    def save_documents_to_file(self, documents: List[Dict[str, Any]], output_file: str):
        """Save processed documents to a file."""
        with open(output_file, 'w') as f:
            json.dump(documents, f, indent=2)
        
        logger.info(f"Saved {len(documents)} documents to {output_file}")
    
    def create_embeddings_for_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for all documents."""
        enhanced_docs = []
        
        for doc in documents:
            try:
                embedding = self.create_embedding(doc["content"])
                enhanced_doc = {
                    **doc,
                    "embedding": embedding
                }
                enhanced_docs.append(enhanced_doc)
                logger.info(f"Created embedding for document: {doc['id']}")
            except Exception as e:
                logger.error(f"Failed to create embedding for {doc['id']}: {str(e)}")
        
        return enhanced_docs


def create_sample_ticket_files():
    """Create sample ticket data files for testing."""
    
    # Create sample JSON data
    sample_json = {
        "teams": {
            "lakers": {
                "home_venue": "Crypto.com Arena",
                "city": "Los Angeles",
                "conference": "Western",
                "division": "Pacific"
            },
            "warriors": {
                "home_venue": "Chase Center", 
                "city": "San Francisco",
                "conference": "Western",
                "division": "Pacific"
            }
        },
        "pricing": {
            "lower_bowl": {"min": 150, "max": 300},
            "upper_bowl": {"min": 50, "max": 120},
            "courtside": {"min": 800, "max": 2000}
        },
        "policies": {
            "refund_hours": 48,
            "upgrade_hours": 2,
            "exchange_fee": 15
        }
    }
    
    with open("sample_ticket_data.json", "w") as f:
        json.dump(sample_json, f, indent=2)
    
    # Create sample CSV data
    sample_csv_data = [
        ["game", "date", "venue", "lower_bowl_price", "upper_bowl_price", "courtside_price"],
        ["Lakers vs Warriors", "2024-03-15", "Crypto.com Arena", "150-300", "50-120", "800-2000"],
        ["Lakers vs Celtics", "2024-03-20", "Crypto.com Arena", "180-350", "60-140", "900-2200"],
        ["Lakers vs Heat", "2024-03-25", "Crypto.com Arena", "160-320", "55-130", "850-2100"]
    ]
    
    with open("sample_ticket_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(sample_csv_data)
    
    # Create sample text data
    sample_text = """
    Lakers Ticket Information
    
    Venue: Crypto.com Arena, Los Angeles, CA
    Capacity: 19,068 for basketball
    
    Pricing Structure:
    - Lower Bowl: $150-300 (sections 101-130)
    - Upper Bowl: $50-120 (sections 301-330) 
    - Courtside: $800-2000 (rows A-F)
    - Club Level: $200-500 (sections 200s)
    
    Policies:
    - Refunds: Up to 48 hours before game
    - Upgrades: Up to 2 hours before game
    - Exchanges: $15 fee, subject to availability
    
    Parking:
    - General: $25-40
    - Premium: $50-75
    - Valet: $60-80
    
    Concessions:
    - Beer: $12-15
    - Soft drinks: $6-8
    - Food: $8-20
    """
    
    with open("sample_ticket_data.txt", "w") as f:
        f.write(sample_text)
    
    print("Created sample files:")
    print("- sample_ticket_data.json")
    print("- sample_ticket_data.csv") 
    print("- sample_ticket_data.txt")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup knowledge base for ticket information")
    parser.add_argument("--create-samples", action="store_true", help="Create sample ticket data files")
    parser.add_argument("--process-file", type=str, help="Process a specific ticket data file")
    parser.add_argument("--output", type=str, default="knowledge_base.json", help="Output file for processed documents")
    parser.add_argument("--create-embeddings", action="store_true", help="Create embeddings for documents")
    
    args = parser.parse_args()
    
    if args.create_samples:
        create_sample_ticket_files()
        print("Sample files created successfully!")
    
    if args.process_file:
        builder = KnowledgeBaseBuilder()
        
        print(f"Processing file: {args.process_file}")
        documents = builder.process_ticket_data(args.process_file)
        
        if args.create_embeddings:
            print("Creating embeddings...")
            documents = builder.create_embeddings_for_documents(documents)
        
        builder.save_documents_to_file(documents, args.output)
        print(f"Processed {len(documents)} documents and saved to {args.output}")
    
    if not args.create_samples and not args.process_file:
        print("Usage examples:")
        print("  python setup_knowledge_base.py --create-samples")
        print("  python setup_knowledge_base.py --process-file sample_ticket_data.json --output my_kb.json")
        print("  python setup_knowledge_base.py --process-file sample_ticket_data.csv --create-embeddings")
