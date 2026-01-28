"""
Example usage of the Events system

This file demonstrates how to use the event system in various scenarios.
"""

from events import EventEmitter, ChatMessageEvent, FilesystemWriteEvent


# ============================================================================
# Example 1: Basic Event Creation
# ============================================================================

def example_basic_events():
    """Create events directly using event classes."""
    
    # Create a chat message event
    chat_event = ChatMessageEvent.create(
        content="Starting project generation...",
        project_id="proj_123",
        conversation_id="conv_456"
    )
    
    # Convert to JSON
    print("Chat Event JSON:")
    print(chat_event.to_json())
    print()
    
    # Create a filesystem write event
    fs_event = FilesystemWriteEvent.create(
        path="src/App.tsx",
        kind="file",
        language="typescript",
        content="export function App() { return <div>Hello World</div>; }",
        project_id="proj_123",
        conversation_id="conv_456"
    )
    
    print("Filesystem Event JSON:")
    print(fs_event.to_json())
    print()


# ============================================================================
# Example 2: Using EventEmitter
# ============================================================================

def example_event_emitter():
    """Use EventEmitter for convenient event generation."""
    
    emitter = EventEmitter(
        project_id="proj_123",
        conversation_id="conv_456"
    )
    
    # Emit chat message
    emitter.emit_chat_message("Starting generation process...")
    
    # Emit thinking events
    emitter.emit_thinking_start()
    # ... do work ...
    emitter.emit_thinking_end(duration_ms=5000)
    
    # Emit progress events
    steps = [
        {"id": "plan", "label": "Planning", "status": "pending"},
        {"id": "code", "label": "Code Generation", "status": "pending"},
    ]
    emitter.emit_progress_init(steps=steps, mode="modal")
    emitter.emit_progress_update(step_id="plan", status="in_progress")
    emitter.emit_progress_update(step_id="plan", status="completed")
    
    # Emit filesystem events
    emitter.emit_fs_create(path="src", kind="folder")
    emitter.emit_fs_write(
        path="src/App.tsx",
        kind="file",
        language="typescript",
        content="export function App() { return <div>Hello</div>; }"
    )
    
    # Emit stream completion
    emitter.emit_stream_complete()


# ============================================================================
# Example 3: SSE Stream with Callback
# ============================================================================

def example_sse_stream():
    """Example of streaming events via SSE with callback."""
    
    def send_to_client(event):
        """Simulate sending event to client via SSE."""
        json_data = event.to_json()
        # In real implementation, send via SSE:
        # yield f"data: {json_data}\n\n"
        print(f"SSE: data: {json_data}")
    
    emitter = EventEmitter(
        project_id="proj_123",
        conversation_id="conv_456",
        callback=send_to_client
    )
    
    # Events are automatically sent via callback
    emitter.emit_chat_message("Processing your request...")
    emitter.emit_fs_write(
        path="src/index.tsx",
        kind="file",
        language="typescript",
        content="import React from 'react';"
    )
    emitter.emit_stream_complete()


# ============================================================================
# Example 4: Complete Generation Flow
# ============================================================================

def example_complete_flow():
    """Example of a complete generation flow with all event types."""
    
    events = []
    
    def collect_events(event):
        events.append(event.to_dict())
    
    emitter = EventEmitter(
        project_id="proj_123",
        conversation_id="conv_456",
        callback=collect_events
    )
    
    # 1. Chat message
    emitter.emit_chat_message("Starting webpage generation...")
    
    # 2. Thinking
    emitter.emit_thinking_start()
    # ... LLM thinking ...
    emitter.emit_thinking_end(duration_ms=3000)
    
    # 3. Progress initialization
    steps = [
        {"id": "plan", "label": "Planning", "status": "pending"},
        {"id": "scaffold", "label": "Scaffolding", "status": "pending"},
        {"id": "code", "label": "Code Generation", "status": "pending"},
        {"id": "verify", "label": "Verification", "status": "pending"},
    ]
    emitter.emit_progress_init(steps=steps, mode="modal")
    
    # 4. Progress updates
    emitter.emit_progress_update("plan", "in_progress")
    emitter.emit_progress_update("plan", "completed")
    emitter.emit_progress_update("scaffold", "in_progress")
    
    # 5. Filesystem operations
    emitter.emit_fs_create("src", "folder")
    emitter.emit_fs_create("src/components", "folder")
    emitter.emit_fs_write(
        path="src/App.tsx",
        kind="file",
        language="typescript",
        content="export function App() { return <div>Hello</div>; }"
    )
    
    # 6. Edit timeline (for chat UI)
    emitter.emit_edit_read("src/App.tsx")
    emitter.emit_edit_start("src/App.tsx", "export function App()")
    emitter.emit_edit_end("src/App.tsx", duration_ms=2000)
    emitter.emit_edit_security_check("src/App.tsx", "passed")
    
    # 7. Progress completion
    emitter.emit_progress_update("scaffold", "completed")
    emitter.emit_progress_update("code", "in_progress")
    emitter.emit_progress_update("code", "completed")
    emitter.emit_progress_update("verify", "completed")
    
    # 8. Transition to inline
    emitter.emit_progress_transition("inline")
    
    # 9. Completion
    emitter.emit_chat_message("Generation complete!")
    emitter.emit_stream_complete()
    
    # Return all events (in real scenario, these would be sent via SSE)
    return events


# ============================================================================
# Example 5: Error Handling
# ============================================================================

def example_error_handling():
    """Example of error event handling."""
    
    emitter = EventEmitter(
        project_id="proj_123",
        conversation_id="conv_456"
    )
    
    try:
        # ... operation that might fail ...
        raise ValueError("Something went wrong")
    except Exception as e:
        # Emit error event
        emitter.emit_error(
            scope="llm",
            message="Generation failed",
            details=str(e),
            actions=["retry", "ask_user"]
        )
        emitter.emit_stream_failed()


# ============================================================================
# Example 6: Backend Events (Build, Preview, etc.)
# ============================================================================

def example_backend_events():
    """Example of backend-only events."""
    
    emitter = EventEmitter(
        project_id="proj_123",
        conversation_id="conv_456"
    )
    
    # Build events
    emitter.emit_build_start(container_id="ctr_001")
    emitter.emit_build_log(level="info", message="Installing dependencies...")
    emitter.emit_build_log(level="info", message="Building project...")
    
    # Preview ready
    emitter.emit_preview_ready(url="https://preview.platform.ai/proj_123", port=5173)
    
    # Version events
    emitter.emit_version_created(version_id="v1", label="Initial Stable", status="stable")
    emitter.emit_version_deployed(version_id="v1", environment="production")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Example 1: Basic Event Creation")
    print("=" * 60)
    example_basic_events()
    
    print("\n" + "=" * 60)
    print("Example 2: EventEmitter Usage")
    print("=" * 60)
    example_event_emitter()
    
    print("\n" + "=" * 60)
    print("Example 3: SSE Stream")
    print("=" * 60)
    example_sse_stream()
    
    print("\n" + "=" * 60)
    print("Example 4: Complete Flow")
    print("=" * 60)
    events = example_complete_flow()
    print(f"Generated {len(events)} events")
    print("\nFirst event:")
    import json
    print(json.dumps(events[0], indent=2))


