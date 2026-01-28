# Events System

This directory contains the complete event system implementation for Phase 1 LLM Streaming Contract.

## Files

- **`event_types.py`** - Python event type definitions and factory functions
- **`event_emitter.py`** - Event emitter utility class for convenient event generation
- **`types.ts`** - TypeScript type definitions for frontend team
- **`EVENT_CONTRACT.md`** - Complete event contract documentation
- **`__init__.py`** - Python module exports

## Quick Start

### Python (Backend/LLM)

#### Using Event Classes Directly

```python
from events import ChatMessageEvent, FilesystemWriteEvent, StreamCompleteEvent

# Create events
chat_event = ChatMessageEvent.create(
    content="Starting generation...",
    project_id="proj_123",
    conversation_id="conv_456"
)

fs_event = FilesystemWriteEvent.create(
    path="src/App.tsx",
    kind="file",
    language="typescript",
    content="export function App() { return <div>Hello</div>; }",
    project_id="proj_123",
    conversation_id="conv_456"
)

complete_event = StreamCompleteEvent.create(
    project_id="proj_123",
    conversation_id="conv_456"
)

# Convert to JSON for SSE
print(chat_event.to_json())
print(fs_event.to_json())
print(complete_event.to_json())
```

#### Using EventEmitter (Recommended)

```python
from events import EventEmitter

# Create emitter with project/conversation context
emitter = EventEmitter(
    project_id="proj_123",
    conversation_id="conv_456"
)

# Emit events easily
emitter.emit_chat_message("Starting generation...")
emitter.emit_thinking_start()

# ... do work ...

emitter.emit_thinking_end(duration_ms=5000)
emitter.emit_fs_write(
    path="src/App.tsx",
    kind="file",
    language="typescript",
    content="export function App() { return <div>Hello</div>; }"
)
emitter.emit_stream_complete()
```

#### With SSE Callback

```python
from events import EventEmitter

def send_sse_event(event):
    """Send event to client via SSE"""
    json_data = event.to_json()
    # Send to client: f"data: {json_data}\n\n"

emitter = EventEmitter(
    project_id="proj_123",
    conversation_id="conv_456",
    callback=send_sse_event
)

# Events are automatically sent via callback
emitter.emit_chat_message("Processing...")
emitter.emit_stream_complete()
```

### TypeScript (Frontend)

```typescript
import {
  EventEnvelope,
  isChatMessageEvent,
  isFilesystemWriteEvent,
  isStreamCompleteEvent,
  isTerminalEvent
} from './events/types';

// Handle incoming events from SSE
function handleEvent(event: EventEnvelope) {
  // Use type guards for type-safe handling
  if (isChatMessageEvent(event)) {
    displayChatMessage(event.payload.content);
  } else if (isFilesystemWriteEvent(event)) {
    updateFileSystem(event.payload.path, event.payload.content);
  } else if (isStreamCompleteEvent(event)) {
    enableUserInput();
  }
  
  // Check if this is a terminal event
  if (isTerminalEvent(event)) {
    // Re-enable user input
    enableUserInput();
  }
}

// Example SSE client
const eventSource = new EventSource('/api/stream');
eventSource.onmessage = (e) => {
  const event: EventEnvelope = JSON.parse(e.data);
  handleEvent(event);
};
```

## Event Categories

### LLM-Emitted Events
- Chat & Cognition: `chat.message`, `thinking.start`, `thinking.end`
- Progress: `progress.init`, `progress.update`, `progress.transition`
- Filesystem: `fs.create`, `fs.write`, `fs.delete`
- Edit Timeline: `edit.read`, `edit.start`, `edit.end`, `edit.security_check`
- Suggestions: `suggestion`, `ui.multiselect`
- Errors: `error` (scope: `llm`)
- Stream Lifecycle: `stream.complete`, `stream.await_input`, `stream.failed`

### Backend-Only Events
- Build: `build.start`, `build.log`, `build.error`
- Preview: `preview.ready`
- Version: `version.created`, `version.deployed`
- Errors: `error` (scope: `runtime`, `validation`, `build`)

## Terminal Events

These events stop the stream and allow user input:
- `stream.complete`
- `stream.await_input`
- `stream.failed`

The frontend MUST wait for one of these events before re-enabling user input.

## SSE Format

Events should be sent over Server-Sent Events (SSE) in this format:

```
data: {"event_id":"evt_0001","event_type":"chat.message","timestamp":"2025-01-04T10:15:30Z","payload":{"content":"Starting..."}}

data: {"event_id":"evt_0002","event_type":"fs.write","timestamp":"2025-01-04T10:15:31Z","payload":{"path":"src/App.tsx","kind":"file","language":"typescript","content":"..."}}

```

Each event should be on a separate line starting with `data: ` followed by the JSON-encoded event envelope.

## Complete Documentation

See `EVENT_CONTRACT.md` for complete event contract documentation with all event types, payloads, and examples.

## Type Safety

- **Python**: Use the event classes and type hints in `event_types.py`
- **TypeScript**: Import types from `types.ts` and use type guards for runtime type checking

## Examples

See `EVENT_CONTRACT.md` for detailed examples of each event type.


