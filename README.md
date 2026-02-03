# Webpage Builder AI API

Unified streaming API for generating web projects using multiple LLM model families (Gemini, GPT, Claude) with contract-compliant event streaming.

## Features

- **Multi-Model Family Support**: Seamlessly switch between Gemini, GPT, and Claude
- **Contract-Compliant Streaming**: Follows Phase 1 LLM Streaming Contract with Universal Event Envelope
- **Action Inference**: No need to specify action - inferred from payload structure
- **Unified Endpoint**: Single `POST /api/v1/stream` endpoint for all operations
- **Real-time Events**: Server-Sent Events (SSE) with proper event types

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requiremnets.txt
```

### Environment Variables

Set up environment variables for your desired model families:

**For Gemini:**
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # Optional
```

**For GPT:**
```bash
export OPENAI_API_KEY="sk-..."
```

**For Claude:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Run API

```bash
# Using the startup script
./start_api.sh

# Or directly
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## API Usage

### Single Unified Endpoint

All operations use `POST /api/v1/stream` with action inferred from payload.

### First Request (Start)

```json
{
  "model_family": "gemini",
  "user_input": "I want to build an e-commerce website",
  "project_id": "proj_123"
}
```

**Response:** SSE stream with events:
- `chat.message` - Status messages
- `thinking.start` / `thinking.end` - Thinking indicators
- `chat.question` - Questions if questionnaire needed
- `ui.multiselect` - Page type selection if generic
- `stream.await_input` - Waiting for user response

### Follow-up Request (After Questions)

```json
{
  "model_family": "gemini",
  "page_type_key": "ecommerce",
  "questionnaire_answers": {
    "target_audience": "young_adults",
    "product_categories": ["electronics", "clothing"]
  },
  "wizard_inputs": {
    "hero_text": "Welcome to our store",
    "theme": "Light"
  }
}
```

**Response:** SSE stream with:
- `progress.init` / `progress.update` - Progress tracking
- `edit.start` - Streaming generation chunks
- `fs.write` - File writes (single source of truth)
- `stream.complete` - Generation finished

### Modify Project

```json
{
  "model_family": "gemini",
  "instruction": "Change the theme to dark mode",
  "base_project_path": "output/project.json"
}
```

## Event Contract

All events follow the Universal Event Envelope format:

```json
{
  "event_id": "evt_abc123",
  "event_type": "chat.message",
  "timestamp": "2025-01-04T10:15:30Z",
  "project_id": "proj_123",
  "conversation_id": "conv_456",
  "payload": {
    "content": "Starting generation..."
  }
}
```

See `events/EVENT_CONTRACT.md` for complete event documentation.

## Model Families

### Gemini (Default)
- Provider: Google Vertex AI
- Required: `GOOGLE_CLOUD_PROJECT`
- Models: `gemini-2.0-flash-lite`, `gemini-3-pro-preview`

### GPT
- Provider: OpenAI
- Required: `OPENAI_API_KEY`
- Models: `gpt-4o-mini`, `gpt-4o`

### Claude
- Provider: Anthropic
- Required: `ANTHROPIC_API_KEY`
- Models: `claude-3-haiku-20240307`, `claude-3-5-sonnet-20241022`

## Project Structure

```
.
├── api.py                 # Main FastAPI application
├── models/                # Model provider abstraction
│   ├── base_provider.py  # Abstract base class
│   ├── model_factory.py  # Provider factory
│   ├── unified_client.py # Unified client interface
│   └── providers/        # Model family implementations
├── events/                # Event contract definitions
│   ├── event_types.py    # Event type classes
│   ├── event_emitter.py  # Event emitter utility
│   └── EVENT_CONTRACT.md # Complete contract docs
├── data/                  # Page types and questionnaires
├── utils/                 # Utilities (logging, etc.)
└── requiremnets.txt      # Dependencies
```

## Testing

Use the provided Postman collection (`Postman_Collection.json`) or see `Postman_Examples.md` for examples.

## Documentation

- `API_README.md` - API documentation
- `MODEL_FAMILY_GUIDE.md` - Model family usage guide
- `events/EVENT_CONTRACT.md` - Complete event contract
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details

## License

[Add your license here]




