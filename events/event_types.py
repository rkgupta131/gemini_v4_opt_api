"""
Event Type Definitions

Defines all event types according to Phase 1 LLM Streaming Contract.
Each event type follows the Universal Event Envelope structure.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Literal


# ============================================================================
# Universal Event Envelope
# ============================================================================

class EventEnvelope:
    """
    Universal event envelope that wraps all events.
    
    Every event streamed from backend to frontend MUST follow this envelope.
    The frontend routes behavior strictly using `event_type`.
    """
    
    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        self.event_id = event_id or f"evt_{uuid.uuid4().hex[:8]}"
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.payload = payload
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary format for JSON serialization."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }
        if self.project_id:
            result["project_id"] = self.project_id
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
        return result
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        import json
        return json.dumps(self.to_dict())


def create_event_envelope(
    event_type: str,
    payload: Dict[str, Any],
    project_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> EventEnvelope:
    """Factory function to create an event envelope."""
    return EventEnvelope(
        event_type=event_type,
        payload=payload,
        project_id=project_id,
        conversation_id=conversation_id,
    )


# ============================================================================
# Chat & Cognition Events
# ============================================================================

class ChatMessageEvent:
    """
    Used for human-readable narration only. No logic is derived from this event.
    """
    
    @staticmethod
    def create(
        content: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="chat.message",
            payload={"content": content},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class ThinkingStartEvent:
    """
    Thinking events are used purely for UX feedback.
    thinking.start → Show 'Thinking…'
    """
    
    @staticmethod
    def create(
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="thinking.start",
            payload={},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class ThinkingEndEvent:
    """
    Thinking events are used purely for UX feedback.
    thinking.end → Show 'Thought for X seconds'
    """
    
    @staticmethod
    def create(
        duration_ms: int,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="thinking.end",
            payload={"duration_ms": duration_ms},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class ChatQuestionEvent:
    """
    LLM-driven question event that blocks the stream until resolved.
    Used for gathering additional information before webpage generation.
    
    According to LLM_Question_Streaming_Contract_FULL:
    - Blocks stream until user answers or skips (if skippable)
    - Frontend enters awaiting_question state
    - Backend pauses emitting further events
    """
    
    @staticmethod
    def create(
        q_id: str,
        question_type: Literal["open_ended", "mcq", "multi_select", "form"],
        label: str,
        is_skippable: bool,
        content: Dict[str, Any],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        """
        Create a chat question event.
        
        Args:
            q_id: Unique question identifier
            question_type: Type of question (open_ended, mcq, multi_select, form)
            label: Question text/label
            is_skippable: Whether the question can be skipped
            content: Question-specific content (options for mcq/multi_select, fields for form)
            project_id: Optional project identifier
            conversation_id: Optional conversation identifier
        """
        return create_event_envelope(
            event_type="chat.question",
            payload={
                "q_id": q_id,
                "type": question_type,
                "label": label,
                "isSkippable": is_skippable,
                "content": content,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class ChatSuggestionEvent:
    """
    LLM-driven suggestion event that blocks the stream until resolved.
    Similar to chat.question but rendered with a different UI component.
    
    According to LLM_Question_Streaming_Contract_FULL:
    - Behaves logically like multi-select
    - Rendered with a different UI component
    - Blocking until answered or skipped
    """
    
    @staticmethod
    def create(
        q_id: str,
        label: str,
        options: List[str],
        is_skippable: bool = True,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        """
        Create a chat suggestion event.
        
        Args:
            q_id: Unique suggestion identifier
            label: Suggestion text/label
            options: List of suggestion options
            is_skippable: Whether the suggestion can be skipped
            project_id: Optional project identifier
            conversation_id: Optional conversation identifier
        """
        return create_event_envelope(
            event_type="chat.suggestion",
            payload={
                "q_id": q_id,
                "type": "multi_select",
                "label": label,
                "isSkippable": is_skippable,
                "content": {
                    "options": options,
                },
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Progress & Planning Events
# ============================================================================

class ProgressInitEvent:
    """
    Progress events visualize execution steps.
    Progress may initially appear as a modal and later transition inline into chat.
    """
    
    @staticmethod
    def create(
        steps: List[Dict[str, Any]],
        mode: Literal["modal", "inline"] = "modal",
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="progress.init",
            payload={
                "mode": mode,
                "steps": steps,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class ProgressUpdateEvent:
    """
    Update the status of a specific progress step.
    """
    
    @staticmethod
    def create(
        step_id: str,
        status: Literal["pending", "in_progress", "completed", "failed"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="progress.update",
            payload={
                "step_id": step_id,
                "status": status,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class ProgressTransitionEvent:
    """
    Transition progress display mode (e.g., from modal to inline).
    """
    
    @staticmethod
    def create(
        mode: Literal["modal", "inline"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="progress.transition",
            payload={"mode": mode},
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Filesystem Events (Monaco + Backend)
# ============================================================================

class FilesystemCreateEvent:
    """
    Filesystem events define the REAL project structure.
    Monaco editor and backend container filesystem must stay perfectly in sync.
    
    IMPORTANT: `fs.write` is the SINGLE SOURCE OF TRUTH for code.
    """
    
    @staticmethod
    def create(
        path: str,
        kind: Literal["file", "folder"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="fs.create",
            payload={
                "path": path,
                "kind": kind,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class FilesystemWriteEvent:
    """
    Filesystem events define the REAL project structure.
    Monaco editor and backend container filesystem must stay perfectly in sync.
    
    IMPORTANT: `fs.write` is the SINGLE SOURCE OF TRUTH for code.
    """
    
    @staticmethod
    def create(
        path: str,
        kind: Literal["file", "folder"],
        language: Optional[str] = None,
        content: Optional[str] = None,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        payload = {
            "path": path,
            "kind": kind,
        }
        if language:
            payload["language"] = language
        if content is not None:
            payload["content"] = content
        
        return create_event_envelope(
            event_type="fs.write",
            payload=payload,
            project_id=project_id,
            conversation_id=conversation_id,
        )


class FilesystemDeleteEvent:
    """
    Delete a file or folder from the filesystem.
    """
    
    @staticmethod
    def create(
        path: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="fs.delete",
            payload={"path": path},
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Edit Timeline Events (Chat – Edits Made Panel)
# ============================================================================

class EditReadEvent:
    """
    Edit events power the 'Edits Made' panel in the chat UI.
    They are NOT the source of truth for code.
    """
    
    @staticmethod
    def create(
        path: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="edit.read",
            payload={"path": path},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class EditStartEvent:
    """
    Edit events power the 'Edits Made' panel in the chat UI.
    They are NOT the source of truth for code.
    
    `edit.start` may be emitted multiple times with content chunks to animate typing in the chat panel.
    """
    
    @staticmethod
    def create(
        path: str,
        content: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="edit.start",
            payload={
                "path": path,
                "content": content,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class EditEndEvent:
    """
    Edit events power the 'Edits Made' panel in the chat UI.
    They are NOT the source of truth for code.
    """
    
    @staticmethod
    def create(
        path: str,
        duration_ms: int,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="edit.end",
            payload={
                "path": path,
                "duration_ms": duration_ms,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class EditSecurityCheckEvent:
    """
    Security check result for an edit operation.
    """
    
    @staticmethod
    def create(
        path: str,
        status: Literal["passed", "failed"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="edit.security_check",
            payload={
                "path": path,
                "status": status,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Build, Preview & Logs Events (Backend-owned)
# ============================================================================

class BuildStartEvent:
    """
    The following events are emitted ONLY by backend services.
    LLM MUST NEVER emit or control these events.
    """
    
    @staticmethod
    def create(
        container_id: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="build.start",
            payload={"container_id": container_id},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class BuildLogEvent:
    """
    Build log messages from the build process.
    """
    
    @staticmethod
    def create(
        level: Literal["info", "warning", "error", "debug"],
        message: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="build.log",
            payload={
                "level": level,
                "message": message,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class BuildErrorEvent:
    """
    Build error event.
    """
    
    @staticmethod
    def create(
        message: str,
        details: Optional[str] = None,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        payload = {"message": message}
        if details:
            payload["details"] = details
        
        return create_event_envelope(
            event_type="build.error",
            payload=payload,
            project_id=project_id,
            conversation_id=conversation_id,
        )


class PreviewReadyEvent:
    """
    Preview URL is ready.
    """
    
    @staticmethod
    def create(
        url: str,
        port: Optional[int] = None,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        payload = {"url": url}
        if port is not None:
            payload["port"] = port
        
        return create_event_envelope(
            event_type="preview.ready",
            payload=payload,
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Version & Deployment Events (Backend-owned)
# ============================================================================

class VersionCreatedEvent:
    """
    Versioning and deployment lifecycle are backend-owned and fully decoupled from LLM behavior.
    """
    
    @staticmethod
    def create(
        version_id: str,
        label: str,
        status: Literal["stable", "unstable", "draft"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="version.created",
            payload={
                "version_id": version_id,
                "label": label,
                "status": status,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class VersionDeployedEvent:
    """
    Version deployment event.
    """
    
    @staticmethod
    def create(
        version_id: str,
        environment: Literal["production", "staging", "development"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="version.deployed",
            payload={
                "version_id": version_id,
                "environment": environment,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Suggestions & User Interaction Events
# ============================================================================

class SuggestionEvent:
    """
    Suggestion event for user interaction.
    """
    
    @staticmethod
    def create(
        suggestion_id: str,
        label: str,
        options: List[str],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="suggestion",
            payload={
                "id": suggestion_id,
                "label": label,
                "options": options,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


class UIMultiselectEvent:
    """
    Multiselect UI event for user interaction.
    """
    
    @staticmethod
    def create(
        select_id: str,
        title: str,
        options: List[Dict[str, str]],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="ui.multiselect",
            payload={
                "id": select_id,
                "title": title,
                "options": options,
            },
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Error Events
# ============================================================================

class ErrorEvent:
    """
    Error event for issues and recovery.
    """
    
    @staticmethod
    def create(
        scope: Literal["runtime", "llm", "validation", "build"],
        message: str,
        details: Optional[str] = None,
        actions: Optional[List[Literal["retry", "ask_user", "auto_fix"]]] = None,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        payload = {
            "scope": scope,
            "message": message,
        }
        if details:
            payload["details"] = details
        if actions:
            payload["actions"] = actions
        
        return create_event_envelope(
            event_type="error",
            payload=payload,
            project_id=project_id,
            conversation_id=conversation_id,
        )


# ============================================================================
# Stream Lifecycle & Input Control Events
# ============================================================================

class StreamCompleteEvent:
    """
    Frontend MUST re-enable user input ONLY after receiving one of the following terminal events.
    """
    
    @staticmethod
    def create(
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="stream.complete",
            payload={},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class StreamAwaitInputEvent:
    """
    Frontend MUST re-enable user input ONLY after receiving one of the following terminal events.
    """
    
    @staticmethod
    def create(
        reason: Literal["suggestion", "multiselect"],
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="stream.await_input",
            payload={"reason": reason},
            project_id=project_id,
            conversation_id=conversation_id,
        )


class StreamFailedEvent:
    """
    Frontend MUST re-enable user input ONLY after receiving one of the following terminal events.
    """
    
    @staticmethod
    def create(
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> EventEnvelope:
        return create_event_envelope(
            event_type="stream.failed",
            payload={},
            project_id=project_id,
            conversation_id=conversation_id,
        )


