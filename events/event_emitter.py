"""
Event Emitter Utilities

Provides utilities for emitting events in a consistent way.
"""

from typing import Optional, Callable, Generator
from .event_types import EventEnvelope


class EventEmitter:
    """
    Event emitter that can be used to stream events.
    
    Usage:
        emitter = EventEmitter(project_id="proj_123", conversation_id="conv_456")
        emitter.emit_chat_message("Starting generation...")
        emitter.emit_thinking_start()
        # ... process ...
        emitter.emit_thinking_end(duration_ms=5000)
        emitter.emit_stream_complete()
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        callback: Optional[Callable[[EventEnvelope], None]] = None,
    ):
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.callback = callback
        self._event_counter = 0
    
    def emit(self, event: EventEnvelope) -> EventEnvelope:
        """Emit an event and call the callback if set."""
        if self.callback:
            self.callback(event)
        return event
    
    # Chat & Cognition Events
    def emit_chat_message(self, content: str) -> EventEnvelope:
        """Emit a chat message event."""
        from .event_types import ChatMessageEvent
        event = ChatMessageEvent.create(
            content=content,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_thinking_start(self) -> EventEnvelope:
        """Emit a thinking start event."""
        from .event_types import ThinkingStartEvent
        event = ThinkingStartEvent.create(
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_thinking_end(self, duration_ms: int) -> EventEnvelope:
        """Emit a thinking end event."""
        from .event_types import ThinkingEndEvent
        event = ThinkingEndEvent.create(
            duration_ms=duration_ms,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_chat_question(
        self,
        q_id: str,
        question_type: str,
        label: str,
        is_skippable: bool,
        content: dict,
    ) -> EventEnvelope:
        """Emit a chat question event (blocks stream until answered)."""
        from .event_types import ChatQuestionEvent
        event = ChatQuestionEvent.create(
            q_id=q_id,
            question_type=question_type,
            label=label,
            is_skippable=is_skippable,
            content=content,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_chat_suggestion(
        self,
        q_id: str,
        label: str,
        options: list,
        is_skippable: bool = True,
    ) -> EventEnvelope:
        """Emit a chat suggestion event (blocks stream until answered)."""
        from .event_types import ChatSuggestionEvent
        event = ChatSuggestionEvent.create(
            q_id=q_id,
            label=label,
            options=options,
            is_skippable=is_skippable,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Progress Events
    def emit_progress_init(self, steps: list, mode: str = "modal") -> EventEnvelope:
        """Emit a progress init event."""
        from .event_types import ProgressInitEvent
        event = ProgressInitEvent.create(
            steps=steps,
            mode=mode,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_progress_update(self, step_id: str, status: str) -> EventEnvelope:
        """Emit a progress update event."""
        from .event_types import ProgressUpdateEvent
        event = ProgressUpdateEvent.create(
            step_id=step_id,
            status=status,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_progress_transition(self, mode: str) -> EventEnvelope:
        """Emit a progress transition event."""
        from .event_types import ProgressTransitionEvent
        event = ProgressTransitionEvent.create(
            mode=mode,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Filesystem Events
    def emit_fs_create(self, path: str, kind: str) -> EventEnvelope:
        """Emit a filesystem create event."""
        from .event_types import FilesystemCreateEvent
        event = FilesystemCreateEvent.create(
            path=path,
            kind=kind,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_fs_write(self, path: str, kind: str, language: Optional[str] = None, content: Optional[str] = None) -> EventEnvelope:
        """Emit a filesystem write event."""
        from .event_types import FilesystemWriteEvent
        event = FilesystemWriteEvent.create(
            path=path,
            kind=kind,
            language=language,
            content=content,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_fs_delete(self, path: str) -> EventEnvelope:
        """Emit a filesystem delete event."""
        from .event_types import FilesystemDeleteEvent
        event = FilesystemDeleteEvent.create(
            path=path,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Edit Events
    def emit_edit_read(self, path: str) -> EventEnvelope:
        """Emit an edit read event."""
        from .event_types import EditReadEvent
        event = EditReadEvent.create(
            path=path,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_edit_start(self, path: str, content: str) -> EventEnvelope:
        """Emit an edit start event."""
        from .event_types import EditStartEvent
        event = EditStartEvent.create(
            path=path,
            content=content,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_edit_end(self, path: str, duration_ms: int) -> EventEnvelope:
        """Emit an edit end event."""
        from .event_types import EditEndEvent
        event = EditEndEvent.create(
            path=path,
            duration_ms=duration_ms,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_edit_security_check(self, path: str, status: str) -> EventEnvelope:
        """Emit an edit security check event."""
        from .event_types import EditSecurityCheckEvent
        event = EditSecurityCheckEvent.create(
            path=path,
            status=status,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Build Events (Backend-owned)
    def emit_build_start(self, container_id: str) -> EventEnvelope:
        """Emit a build start event."""
        from .event_types import BuildStartEvent
        event = BuildStartEvent.create(
            container_id=container_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_build_log(self, level: str, message: str) -> EventEnvelope:
        """Emit a build log event."""
        from .event_types import BuildLogEvent
        event = BuildLogEvent.create(
            level=level,
            message=message,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_build_error(self, message: str, details: Optional[str] = None) -> EventEnvelope:
        """Emit a build error event."""
        from .event_types import BuildErrorEvent
        event = BuildErrorEvent.create(
            message=message,
            details=details,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_preview_ready(self, url: str, port: Optional[int] = None) -> EventEnvelope:
        """Emit a preview ready event."""
        from .event_types import PreviewReadyEvent
        event = PreviewReadyEvent.create(
            url=url,
            port=port,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Version Events (Backend-owned)
    def emit_version_created(self, version_id: str, label: str, status: str) -> EventEnvelope:
        """Emit a version created event."""
        from .event_types import VersionCreatedEvent
        event = VersionCreatedEvent.create(
            version_id=version_id,
            label=label,
            status=status,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_version_deployed(self, version_id: str, environment: str) -> EventEnvelope:
        """Emit a version deployed event."""
        from .event_types import VersionDeployedEvent
        event = VersionDeployedEvent.create(
            version_id=version_id,
            environment=environment,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Suggestion & UI Events
    def emit_suggestion(self, suggestion_id: str, label: str, options: list) -> EventEnvelope:
        """Emit a suggestion event."""
        from .event_types import SuggestionEvent
        event = SuggestionEvent.create(
            suggestion_id=suggestion_id,
            label=label,
            options=options,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_ui_multiselect(self, select_id: str, title: str, options: list) -> EventEnvelope:
        """Emit a UI multiselect event."""
        from .event_types import UIMultiselectEvent
        event = UIMultiselectEvent.create(
            select_id=select_id,
            title=title,
            options=options,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Error Events
    def emit_error(self, scope: str, message: str, details: Optional[str] = None, actions: Optional[list] = None) -> EventEnvelope:
        """Emit an error event."""
        from .event_types import ErrorEvent
        event = ErrorEvent.create(
            scope=scope,
            message=message,
            details=details,
            actions=actions,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    # Stream Lifecycle Events
    def emit_stream_complete(self) -> EventEnvelope:
        """Emit a stream complete event."""
        from .event_types import StreamCompleteEvent
        event = StreamCompleteEvent.create(
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_stream_await_input(self, reason: str) -> EventEnvelope:
        """Emit a stream await input event."""
        from .event_types import StreamAwaitInputEvent
        event = StreamAwaitInputEvent.create(
            reason=reason,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)
    
    def emit_stream_failed(self) -> EventEnvelope:
        """Emit a stream failed event."""
        from .event_types import StreamFailedEvent
        event = StreamFailedEvent.create(
            project_id=self.project_id,
            conversation_id=self.conversation_id,
        )
        return self.emit(event)


# Global event emitter instance (can be set by application)
_default_emitter: Optional[EventEmitter] = None


def get_event_emitter(
    project_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> EventEmitter:
    """Get or create the default event emitter."""
    global _default_emitter
    if _default_emitter is None:
        _default_emitter = EventEmitter(project_id=project_id, conversation_id=conversation_id)
    return _default_emitter


def set_event_emitter(emitter: EventEmitter) -> None:
    """Set the default event emitter."""
    global _default_emitter
    _default_emitter = emitter


