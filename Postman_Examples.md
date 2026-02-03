# Postman Collection Examples

## Import Instructions

1. Open Postman
2. Click **Import** button
3. Select the `Postman_Collection.json` file
4. The collection will be imported with all examples

## Environment Variable

Set the `base_url` variable in Postman:
- Default: `http://localhost:8000`
- Or create a Postman Environment with `base_url` variable

## Request Examples

### 1. Stream - Classify Intent

**Endpoint:** `POST /api/v1/stream`

**Request Body:**
```json
{
  "action": "classify_intent",
  "session_id": "session_123",
  "user_input": "I want to build an e-commerce website"
}
```

**Expected Response (SSE Stream):**
```
data: {"type": "intent_classified", "label": "webpage_build", "meta": {...}}
data: {"type": "page_type_classified", "page_type_key": "ecommerce", "meta": {...}}
data: {"type": "question", "question_id": "q1", "question": "...", "options": [...]}
data: {"type": "stream_complete"}
```

### 2. Stream - Chat

**Endpoint:** `POST /api/v1/stream`

**Request Body:**
```json
{
  "action": "chat",
  "session_id": "session_123",
  "user_input": "What is React and how does it work?"
}
```

**Expected Response (SSE Stream):**
```
data: {"type": "thinking_start"}
data: {"type": "chat_chunk", "content": "React is a JavaScript library..."}
data: {"type": "chat_chunk", "content": " for building user interfaces."}
data: {"type": "thinking_end", "duration_ms": 1000}
data: {"type": "chat_complete", "content": "...", "model": "..."}
data: {"type": "stream_complete"}
```

### 3. Stream - Generate Project (Basic)

**Endpoint:** `POST /api/v1/stream`

**Request Body:**
```json
{
  "action": "generate_project",
  "session_id": "session_123",
  "page_type_key": "ecommerce",
  "wizard_inputs": {
    "hero_text": "Welcome to our store",
    "subtext": "Best products at best prices",
    "cta": "Shop Now",
    "theme": "Light"
  }
}
```

**Expected Response (SSE Stream):**
```
data: {"type": "progress_init", "steps": [...]}
data: {"type": "progress_update", "step_id": "prepare", "status": "completed"}
data: {"type": "progress_update", "step_id": "generate", "status": "in_progress"}
data: {"type": "thinking_start"}
data: {"type": "generation_chunk", "content": "{"}
data: {"type": "generation_chunk", "content": "\"project\""}
...
data: {"type": "project_generated", "project_path": "...", "files_count": 25}
data: {"type": "stream_complete"}
```

### 4. Stream - Generate Project (With Questionnaire)

**Endpoint:** `POST /api/v1/stream`

**Request Body:**
```json
{
  "action": "generate_project",
  "session_id": "session_123",
  "page_type_key": "ecommerce",
  "questionnaire_answers": {
    "target_audience": "young_adults",
    "product_categories": ["electronics", "clothing"],
    "payment_methods": "credit_card"
  },
  "wizard_inputs": {
    "hero_text": "Welcome to our store",
    "subtext": "Best products at best prices",
    "cta": "Shop Now",
    "theme": "Dark"
  }
}
```

### 5. Stream - Modify Project

**Endpoint:** `POST /api/v1/stream`

**Request Body:**
```json
{
  "action": "modify_project",
  "session_id": "session_123",
  "instruction": "Change the theme to dark mode and add a footer with social media links",
  "base_project_path": "output/project.json"
}
```

**Expected Response (SSE Stream):**
```
data: {"type": "modification_start", "complexity": "medium", "model": "..."}
data: {"type": "thinking_start"}
data: {"type": "modification_chunk", "content": "{"}
data: {"type": "modification_chunk", "content": "\"project\""}
...
data: {"type": "modification_complete", "project_path": "...", "files_count": 25}
data: {"type": "stream_complete"}
```

## Testing in Postman

### For Streaming Responses:

1. **Send Request** - Click Send in Postman
2. **View Response** - The response will show as a stream of data
3. **Raw View** - Switch to "Raw" view to see the SSE format
4. **Pretty View** - Switch to "Pretty" view to see formatted JSON (may not work well for streams)

### Note on Streaming:

Postman may not display streaming responses perfectly. For better streaming visualization:
- Use a tool like `curl` with `-N` flag
- Use a browser with EventSource API
- Use a custom client that handles SSE properly

### Example curl command:

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

## Available Actions

- `classify_intent` - Classify user intent and determine next steps
- `chat` - Chat with the AI
- `generate_project` - Generate a new project
- `modify_project` - Modify an existing project

## Session Management

Use the same `session_id` across multiple requests to maintain state:
- First request: `classify_intent` with a new session_id
- If questions are asked, answer them and use the same session_id
- Use the same session_id for `generate_project` to maintain context




