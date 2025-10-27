# Messaging Agent System

Core agent logic with tool calling, RAG, and multi-modal capabilities.

## Components

### Main Agent (`messaging_agent.py`)
- Core conversation logic
- Prompt formatting
- Response generation
- Error handling

### Tools (`tools.py`)
- `check_inventory` - Check ticket availability
- `hold_tickets` - Reserve tickets
- `create_order` - Process purchase
- `upgrade_tickets` - Suggest upgrades
- `release_hold` - Cancel reservation
- `get_event_info` - Event details

### RAG System (`rag.py`)
- Vector search using Vertex AI Vector Search
- Context retrieval from knowledge base
- Enhanced responses with retrieved information

### Multi-Modal (`multimodal.py`)
- Image processing (OCR, QR codes)
- Voice processing (speech-to-text)
- Document processing (PDF parsing)

## Usage

### Basic Chat
```python
from agent.messaging_agent import MessagingAgent

agent = MessagingAgent()
response = agent.chat("I need Lakers tickets", context={})
```

### With Tools
```python
# Agent automatically calls tools when needed
response = agent.chat(
    "Check if Lakers tickets are available",
    tools=ToolRegistry.get_all_tools()
)
```

### With RAG
```python
from agent.rag import RAGAgent

rag_agent = RAGAgent()
response = rag_agent.chat_with_context(
    "What's the refund policy?",
    search_k=3  # Retrieve top 3 relevant chunks
)
```

## Training

### LoRA Fine-Tuning
```bash
cd trainer
python train.py \
  --model_name Qwen/Qwen3-4B-Instruct-2507 \
  --dataset_path ./data/chat_dataset.json \
  --output_dir ./outputs \
  --num_epochs 3 \
  --lora_r 16 \
  --lora_alpha 32
```

### Training Configuration
- **Model**: Qwen3-4B-Instruct-2507
- **Method**: LoRA (Low-Rank Adaptation)
- **Quantization**: 4-bit for memory efficiency
- **Optimizer**: AdamW with learning rate scheduling
- **Validation**: Automatic on validation split

## Agent Capabilities

### Conversation Management
- Context-aware responses
- Multi-turn dialogues
- Intent classification
- Sentiment analysis

### Tool Calling
- Automatic tool selection
- Parameter extraction
- Execution and response formatting
- Error recovery

### Knowledge Integration
- Retrieval augmented generation
- Real-time information
- Fact verification
- Dynamic updates

## Configuration

```python
from agent.messaging_agent import MessagingAgent

agent = MessagingAgent(
    temperature=0.7,
    max_tokens=2000,
    enable_tools=True,
    enable_rag=True,
    rag_top_k=3
)
```

## Documentation

- **[Agent Logic](./messaging_agent.py)** - Core agent implementation
- **[Tools](./tools.py)** - Available tools
- **[RAG System](./rag.py)** - Knowledge retrieval
- **[Multi-Modal](./multimodal.py)** - Multi-modal processing
