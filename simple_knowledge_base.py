"""
Simple Knowledge Base Setup for Ticket Information
This script helps you create and organize ticket data for your RAG system
"""

import os
import json
import csv
from typing import List, Dict, Any, Optional

class SimpleKnowledgeBaseBuilder:
    """Build and manage knowledge base for ticket information."""
    
    def __init__(self):
        pass
    
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
        
        print(f"✅ Saved {len(documents)} documents to {output_file}")
    
    def search_documents(self, documents: List[Dict[str, Any]], query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword-based search for testing."""
        query_words = query.lower().split()
        scored_docs = []
        
        for doc in documents:
            content = doc["content"].lower()
            score = sum(1 for word in query_words if word in content)
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and return top_k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]


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
    
    print("✅ Created sample files:")
    print("   - sample_ticket_data.json")
    print("   - sample_ticket_data.csv") 
    print("   - sample_ticket_data.txt")


def test_knowledge_base():
    """Test the knowledge base with sample queries."""
    builder = SimpleKnowledgeBaseBuilder()
    
    # Create sample documents
    documents = builder.create_sample_ticket_data()
    
    # Test queries
    test_queries = [
        "What are the ticket prices?",
        "What's the refund policy?",
        "Where do the Lakers play?",
        "How much does parking cost?",
        "What time do games start?"
    ]
    
    print("\n🔍 Testing Knowledge Base Search:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = builder.search_documents(documents, query, top_k=2)
        
        if results:
            for i, doc in enumerate(results, 1):
                print(f"  {i}. {doc['content'][:100]}...")
        else:
            print("  No results found")
    
    # Save the knowledge base
    builder.save_documents_to_file(documents, "knowledge_base.json")
    
    return documents


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup knowledge base for ticket information")
    parser.add_argument("--create-samples", action="store_true", help="Create sample ticket data files")
    parser.add_argument("--process-file", type=str, help="Process a specific ticket data file")
    parser.add_argument("--output", type=str, default="knowledge_base.json", help="Output file for processed documents")
    parser.add_argument("--test", action="store_true", help="Test the knowledge base with sample queries")
    
    args = parser.parse_args()
    
    if args.create_samples:
        create_sample_ticket_files()
        print("\n✅ Sample files created successfully!")
    
    if args.test:
        test_knowledge_base()
        print("\n✅ Knowledge base test completed!")
    
    if args.process_file:
        builder = SimpleKnowledgeBaseBuilder()
        
        print(f"📁 Processing file: {args.process_file}")
        documents = builder.process_ticket_data(args.process_file)
        
        builder.save_documents_to_file(documents, args.output)
        print(f"✅ Processed {len(documents)} documents and saved to {args.output}")
        
        # Test with a few queries
        print("\n🔍 Quick test with sample queries:")
        test_queries = ["pricing", "policy", "venue"]
        for query in test_queries:
            results = builder.search_documents(documents, query, top_k=1)
            if results:
                print(f"  '{query}' -> {results[0]['content'][:80]}...")
    
    if not any([args.create_samples, args.process_file, args.test]):
        print("🎫 Knowledge Base Setup for Ticket Information")
        print("=" * 50)
        print("\nUsage examples:")
        print("  python3 simple_knowledge_base.py --create-samples")
        print("  python3 simple_knowledge_base.py --test")
        print("  python3 simple_knowledge_base.py --process-file sample_ticket_data.json")
        print("  python3 simple_knowledge_base.py --process-file your_ticket_data.csv --output my_kb.json")
        print("\nNext steps:")
        print("  1. Create sample data: --create-samples")
        print("  2. Test the system: --test")
        print("  3. Process your data: --process-file your_file.json")
        print("  4. Integrate with RAG system in production")
