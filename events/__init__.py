"""
Event System for LLM Streaming Contract

This module provides event definitions and utilities for the Phase 1 streaming contract
between LLM, Backend, and Frontend teams.
"""

from .event_types import (
    # Universal Event Envelope
    EventEnvelope,
    create_event_envelope,
    
    # Chat & Cognition Events
    ChatMessageEvent,
    ThinkingStartEvent,
    ThinkingEndEvent,
    
    # Progress & Planning Events
    ProgressInitEvent,
    ProgressUpdateEvent,
    ProgressTransitionEvent,
    
    # Filesystem Events
    FilesystemCreateEvent,
    FilesystemWriteEvent,
    FilesystemDeleteEvent,
    
    # Edit Timeline Events
    EditReadEvent,
    EditStartEvent,
    EditEndEvent,
    EditSecurityCheckEvent,
    
    # Build, Preview & Logs Events (Backend-owned)
    BuildStartEvent,
    BuildLogEvent,
    BuildErrorEvent,
    PreviewReadyEvent,
    
    # Version & Deployment Events (Backend-owned)
    VersionCreatedEvent,
    VersionDeployedEvent,
    
    # Suggestions & User Interaction Events
    SuggestionEvent,
    UIMultiselectEvent,
    
    # Error Events
    ErrorEvent,
    
    # Stream Lifecycle Events
    StreamCompleteEvent,
    StreamAwaitInputEvent,
    StreamFailedEvent,
)

from .event_emitter import EventEmitter, get_event_emitter

__all__ = [
    "EventEnvelope",
    "create_event_envelope",
    "ChatMessageEvent",
    "ThinkingStartEvent",
    "ThinkingEndEvent",
    "ProgressInitEvent",
    "ProgressUpdateEvent",
    "ProgressTransitionEvent",
    "FilesystemCreateEvent",
    "FilesystemWriteEvent",
    "FilesystemDeleteEvent",
    "EditReadEvent",
    "EditStartEvent",
    "EditEndEvent",
    "EditSecurityCheckEvent",
    "BuildStartEvent",
    "BuildLogEvent",
    "BuildErrorEvent",
    "PreviewReadyEvent",
    "VersionCreatedEvent",
    "VersionDeployedEvent",
    "SuggestionEvent",
    "UIMultiselectEvent",
    "ErrorEvent",
    "StreamCompleteEvent",
    "StreamAwaitInputEvent",
    "StreamFailedEvent",
    "EventEmitter",
    "get_event_emitter",
]


