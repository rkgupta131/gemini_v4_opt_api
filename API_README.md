# Webpage Builder AI API

This is a REST API for generating and modifying web projects using AI. The Streamlit UI has been removed and replaced with FastAPI endpoints.

## Setup

1. Install dependencies:
```bash
pip install -r requiremnets.txt
```

2. Set up environment variables (create a `.env` file):
```
# Add your Google Cloud credentials and API keys here
```

## Running the API

### Option 1: Using the startup script
```bash
./start_api.sh
```

### Option 2: Using uvicorn directly
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- API: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### Root
- `GET /` - API information and available endpoints

### Unified Streaming Endpoint (Main API)
- `POST /api/v1/stream` - **Unified streaming endpoint for all LLM interactions**
  - **Streams all responses using Server-Sent Events (SSE)**
  - **Supports all actions: intent classification, project generation, modifications, chat**
  - Request body:
    ```json
    {
      "action": "classify_intent" | "generate_project" | "modify_project" | "chat",
      "session_id": "string",
      "user_input": "string (required for classify_intent/chat)",
      "page_type_key": "string (optional)",
      "questionnaire_answers": {"question_id": "answer"} (optional),
      "wizard_inputs": {
        "hero_text": "string",
        "subtext": "string",
        "cta": "string",
        "theme": "Light|Dark|Minimal"
      } (optional),
      "instruction": "string (required for modify_project)",
      "base_project_path": "string (optional)"
    }
    ```
  - Response: Server-Sent Events stream with JSON events
  - Event types:
    - `intent_classified` - Intent classification result
    - `question` - Questionnaire question (blocks until answered)
    - `chat_chunk` - Streaming chat response chunks
    - `generation_chunk` - Streaming project generation chunks
    - `modification_chunk` - Streaming modification chunks
    - `progress_init` - Progress initialization
    - `progress_update` - Progress step update
    - `thinking_start` / `thinking_end` - Thinking indicators
    - `project_generated` - Project generation complete
    - `modification_complete` - Modification complete
    - `stream_complete` - Stream finished
    - `error` - Error occurred

### Page Types
- `GET /api/v1/page-types` - Get all available page types/categories

### Questionnaire
- `GET /api/v1/questionnaire/{page_type_key}` - Get questionnaire for a specific page type

### Latest Project
- `GET /api/v1/latest-project` - Get the latest generated project

### Health Check
- `GET /api/v1/health` - Health check endpoint

## Session Management

The API uses in-memory session storage. Each request should include a `session_id` to maintain state across requests. In production, consider using Redis or a database for session management.

## Events

The API generates events during project generation and modification. Events are saved to `output/events.jsonl` in JSONL format. These events can be consumed by frontend/backend applications for real-time updates.

## Example Usage

### Streaming Intent Classification
```bash
curl -X POST "http://localhost:8000/api/v1/stream" \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "action": "classify_intent",
    "session_id": "session_123",
    "user_input": "I want to build an e-commerce website"
  }'
```

### Streaming Project Generation
```bash
curl -X POST "http://localhost:8000/api/v1/stream" \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "action": "generate_project",
    "session_id": "session_123",
    "page_type_key": "ecommerce",
    "wizard_inputs": {
      "hero_text": "Welcome to our store",
      "subtext": "Best products at best prices",
      "cta": "Shop Now",
      "theme": "Light"
    }
  }'
```

### Streaming Chat
```bash
curl -X POST "http://localhost:8000/api/v1/stream" \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "action": "chat",
    "session_id": "session_123",
    "user_input": "What is React?"
  }'
```

### JavaScript/TypeScript Example
```javascript
const response = await fetch('http://localhost:8000/api/v1/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'classify_intent',
    session_id: 'session_123',
    user_input: 'I want to build an e-commerce website'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log('Event:', data);
      
      // Handle different event types
      switch (data.type) {
        case 'intent_classified':
          console.log('Intent:', data.label);
          break;
        case 'question':
          // Show question to user and wait for answer
          break;
        case 'chat_chunk':
          // Append chunk to chat display
          break;
        case 'generation_chunk':
          // Show generation progress
          break;
        case 'stream_complete':
          console.log('Stream completed');
          break;
      }
    }
  }
}
```

## Migration Notes

- The old `app.py` (Streamlit) file is kept for reference but is no longer used
- All Streamlit UI code has been removed
- Session state is now managed via `session_id` in API requests
- Events are still generated and saved to `output/events.jsonl`

## Production Considerations

1. **Session Storage**: Replace in-memory sessions with Redis or database
2. **Authentication**: Add authentication/authorization middleware
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Error Handling**: Enhance error handling and logging
5. **CORS**: Configure CORS for frontend access
6. **Environment Variables**: Use secure secret management

