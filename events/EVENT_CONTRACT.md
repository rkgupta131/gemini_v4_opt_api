# Phase 1 – Complete Streaming & Event Contract

This document defines the COMPLETE and FINAL Phase‑1 streaming contract between the LLM, Backend, and Frontend for the no‑code builder platform.

⚠️ **IMPORTANT**: This is a Phase‑1 contract and MUST be reviewed by Frontend, Backend, AI, Infra, and Product stakeholders before being considered locked.

## Table of Contents

1. [Responsibility Matrix](#1-responsibility-matrix)
2. [Universal Event Envelope](#2-universal-event-envelope)
3. [Chat & Cognition Events](#3-chat--cognition-events)
4. [Progress & Planning Events](#4-progress--planning-events)
5. [Filesystem Events](#5-filesystem-events-monaco--backend)
6. [Edit Timeline Events](#6-edit-timeline-events-chat--edits-made-panel)
7. [Build, Preview & Logs Events](#7-build-preview--logs-events-backend-owned)
8. [Version & Deployment Events](#8-versions--deployment-events-backend-owned)
9. [Suggestions & User Interaction Events](#9-suggestions-modals--user-interaction)
10. [Error Events](#10-errors-issues--recovery)
11. [Stream Lifecycle Events](#11-stream-lifecycle--input-control)

---

## 1. Responsibility Matrix

### LLM (Intent Emitter)
- Emits structured streaming events only
- Does NOT control builds, previews, deployments, or versions

### Backend (Executor & Stream Owner)
- Owns SSE lifecycle
- Validates all incoming LLM events
- Owns filesystem, build, logs, preview URLs, versions

### Frontend (Pure Renderer)
- Renders UI strictly from events
- Never guesses state

---

## 2. Universal Event Envelope

Every event streamed from backend to frontend MUST follow this envelope. The frontend routes behavior strictly using `event_type`.

### Schema

```json
{
  "event_id": "evt_0001",
  "event_type": "chat.message",
  "timestamp": "2025-01-04T10:15:30Z",
  "project_id": "proj_123",
  "conversation_id": "conv_456",
  "payload": {}
}
```

### Fields

- `event_id` (required): Unique identifier for the event (format: `evt_<hex>`)
- `event_type` (required): Type of the event (see event types below)
- `timestamp` (required): ISO 8601 timestamp in UTC
- `project_id` (optional): Project identifier
- `conversation_id` (optional): Conversation/thread identifier
- `payload` (required): Event-specific payload object

---

## 3. Chat & Cognition Events

### 3.1 Chat Message (`chat.message`)

Used for human‑readable narration only. No logic is derived from this event.

**Payload:**
```json
{
  "content": "I am setting up the project structure and dependencies."
}
```

### 3.2 Thinking Start (`thinking.start`)

Thinking events are used purely for UX feedback.
- `thinking.start` → Show 'Thinking…'

**Payload:**
```json
{}
```

### 3.3 Thinking End (`thinking.end`)

- `thinking.end` → Show 'Thought for X seconds'

**Payload:**
```json
{
  "duration_ms": 12000
}
```

---

## 4. Progress & Planning Events

Progress events visualize execution steps. Progress may initially appear as a modal and later transition inline into chat.

### 4.1 Progress Init (`progress.init`)

**Payload:**
```json
{
  "mode": "modal",
  "steps": [
    { "id": "plan", "label": "Planning", "status": "pending" },
    { "id": "scaffold", "label": "Scaffolding", "status": "pending" },
    { "id": "deps", "label": "Dependencies", "status": "pending" },
    { "id": "code", "label": "Code Generation", "status": "pending" },
    { "id": "build", "label": "Build", "status": "pending" },
    { "id": "run", "label": "Preview", "status": "pending" },
    { "id": "verify", "label": "Verification", "status": "pending" }
  ]
}
```

### 4.2 Progress Update (`progress.update`)

**Payload:**
```json
{
  "step_id": "code",
  "status": "in_progress"
}
```

**Status values:** `pending`, `in_progress`, `completed`, `failed`

### 4.3 Progress Transition (`progress.transition`)

**Payload:**
```json
{
  "mode": "inline"
}
```

**Mode values:** `modal`, `inline`

---

## 5. Filesystem Events (Monaco + Backend)

Filesystem events define the REAL project structure. Monaco editor and backend container filesystem must stay perfectly in sync.

**IMPORTANT:** `fs.write` is the SINGLE SOURCE OF TRUTH for code.

### 5.1 Filesystem Create (`fs.create`)

**Payload:**
```json
{
  "path": "src/components/modal",
  "kind": "folder"
}
```

**Kind values:** `file`, `folder`

### 5.2 Filesystem Write (`fs.write`)

**Payload:**
```json
{
  "path": "src/components/modal/Modal.tsx",
  "kind": "file",
  "language": "typescript",
  "content": "export function Modal() { ... }"
}
```

### 5.3 Filesystem Delete (`fs.delete`)

**Payload:**
```json
{
  "path": "src/legacy.tsx"
}
```

---

## 6. Edit Timeline Events (Chat – Edits Made Panel)

Edit events power the 'Edits Made' panel in the chat UI. They are NOT the source of truth for code.

**Note:** `edit.start` may be emitted multiple times with content chunks to animate typing in the chat panel.

### 6.1 Edit Read (`edit.read`)

**Payload:**
```json
{
  "path": "src/Contact.tsx"
}
```

### 6.2 Edit Start (`edit.start`)

**Payload:**
```json
{
  "path": "src/Contact.tsx",
  "content": "export const Contact = () => {"
}
```

### 6.3 Edit End (`edit.end`)

**Payload:**
```json
{
  "path": "src/Contact.tsx",
  "duration_ms": 12000
}
```

### 6.4 Edit Security Check (`edit.security_check`)

**Payload:**
```json
{
  "path": "src/Contact.tsx",
  "status": "passed"
}
```

**Status values:** `passed`, `failed`

---

## 7. Build, Preview & Logs Events (Backend-owned)

The following events are emitted ONLY by backend services. LLM MUST NEVER emit or control these events.

### 7.1 Build Start (`build.start`)

**Payload:**
```json
{
  "container_id": "ctr_001"
}
```

### 7.2 Build Log (`build.log`)

**Payload:**
```json
{
  "level": "info",
  "message": "Installing dependencies..."
}
```

**Level values:** `info`, `warning`, `error`, `debug`

### 7.3 Build Error (`build.error`)

**Payload:**
```json
{
  "message": "Build failed",
  "details": "Missing dependency"
}
```

### 7.4 Preview Ready (`preview.ready`)

**Payload:**
```json
{
  "url": "https://preview.platform.ai/proj_123",
  "port": 5173
}
```

---

## 8. Versions & Deployment Events (Backend-owned)

Versioning and deployment lifecycle are backend‑owned and fully decoupled from LLM behavior.

### 8.1 Version Created (`version.created`)

**Payload:**
```json
{
  "version_id": "v1",
  "label": "Initial Stable",
  "status": "stable"
}
```

**Status values:** `stable`, `unstable`, `draft`

### 8.2 Version Deployed (`version.deployed`)

**Payload:**
```json
{
  "version_id": "v1",
  "environment": "production"
}
```

**Environment values:** `production`, `staging`, `development`

---

## 9. Suggestions, Modals & User Interaction

### 9.1 Suggestion (`suggestion`)

**Payload:**
```json
{
  "id": "next",
  "label": "What do you want to do next?",
  "options": [
    "Add authentication",
    "Enable dark mode"
  ]
}
```

### 9.2 UI Multiselect (`ui.multiselect`)

**Payload:**
```json
{
  "id": "enable_ai",
  "title": "Enable AI",
  "options": [
    { "id": "deps", "label": "Install dependencies" },
    { "id": "routing", "label": "Update routing" }
  ]
}
```

---

## 10. Errors, Issues & Recovery

### 10.1 Error (`error`)

**Payload:**
```json
{
  "scope": "runtime",
  "message": "Users cannot login",
  "details": "Auth misconfigured",
  "actions": ["retry", "ask_user", "auto_fix"]
}
```

**Scope values:** `runtime`, `llm`, `validation`, `build`

**Action values:** `retry`, `ask_user`, `auto_fix`

---

## 11. Stream Lifecycle & Input Control

Frontend MUST re‑enable user input ONLY after receiving one of the following terminal events.

### 11.1 Stream Complete (`stream.complete`)

**Payload:**
```json
{}
```

### 11.2 Stream Await Input (`stream.await_input`)

**Payload:**
```json
{
  "reason": "suggestion"
}
```

**Reason values:** `suggestion`, `multiselect`

### 11.3 Stream Failed (`stream.failed`)

**Payload:**
```json
{}
```

---

## Implementation Notes

### Python (Backend/LLM)

Use the event classes from `events.event_types`:

```python
from events import ChatMessageEvent, FilesystemWriteEvent, StreamCompleteEvent

# Create and emit events
event = ChatMessageEvent.create(
    content="Starting generation...",
    project_id="proj_123",
    conversation_id="conv_456"
)

# Convert to JSON for SSE
json_string = event.to_json()
```

Or use the EventEmitter for convenience:

```python
from events import EventEmitter

emitter = EventEmitter(project_id="proj_123", conversation_id="conv_456")
emitter.emit_chat_message("Starting generation...")
emitter.emit_fs_write(
    path="src/App.tsx",
    kind="file",
    language="typescript",
    content="export function App() { ... }"
)
emitter.emit_stream_complete()
```

### TypeScript (Frontend)

Use the type definitions from `events/types.ts`:

```typescript
import { EventEnvelope, isChatMessageEvent, isStreamCompleteEvent } from './events/types';

function handleEvent(event: EventEnvelope) {
  if (isChatMessageEvent(event)) {
    console.log('Chat message:', event.payload.content);
  } else if (isStreamCompleteEvent(event)) {
    // Re-enable user input
    enableUserInput();
  }
}
```

### SSE Stream Format

Events should be sent over SSE (Server-Sent Events) in the following format:

```
data: {"event_id":"evt_0001","event_type":"chat.message","timestamp":"2025-01-04T10:15:30Z","payload":{"content":"Starting generation..."}}

data: {"event_id":"evt_0002","event_type":"fs.write","timestamp":"2025-01-04T10:15:31Z","payload":{"path":"src/App.tsx","kind":"file","language":"typescript","content":"..."}}

```

Each event should be on a separate line starting with `data: ` followed by the JSON-encoded event envelope.

---

## Event Type Reference

### LLM-Emitted Events
- `chat.message`
- `thinking.start`
- `thinking.end`
- `progress.init`
- `progress.update`
- `progress.transition`
- `fs.create`
- `fs.write`
- `fs.delete`
- `edit.read`
- `edit.start`
- `edit.end`
- `edit.security_check`
- `suggestion`
- `ui.multiselect`
- `error` (scope: `llm`)
- `stream.complete`
- `stream.await_input`
- `stream.failed`

### Backend-Only Events
- `build.start`
- `build.log`
- `build.error`
- `preview.ready`
- `version.created`
- `version.deployed`
- `error` (scope: `runtime`, `validation`, `build`)

---

## Terminal Events

These events stop the stream and allow user input:
- `stream.complete`
- `stream.await_input`
- `stream.failed`

The frontend MUST wait for one of these events before re-enabling user input.

---

## Multi-chunk File Generation

Multi-chunk file generation introduces a risk of out-of-order or missing content during LLM streaming. This requires an explicit platform-level strategy to guarantee deterministic file assembly and avoid broken code.

**Recommendation:** Use file-level locking or sequence numbers for multi-chunk writes to ensure atomic file updates.

---

## Review Status

- [ ] Frontend Team Review
- [ ] Backend Team Review
- [ ] AI/LLM Team Review
- [ ] Infrastructure Team Review
- [ ] Product Team Review

**Last Updated:** Based on Phase1_LLM_Streaming_Contract.docx


