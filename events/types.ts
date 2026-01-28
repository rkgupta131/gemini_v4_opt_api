/**
 * TypeScript Type Definitions for Phase 1 LLM Streaming Contract
 * 
 * This file provides TypeScript type definitions for all events in the streaming contract.
 * Use these types in your frontend code for type safety.
 * 
 * Last updated: Based on Phase1_LLM_Streaming_Contract.docx
 */

// ============================================================================
// Universal Event Envelope
// ============================================================================

export interface EventEnvelope {
  event_id: string;
  event_type: EventType;
  timestamp: string; // ISO 8601 format
  project_id?: string;
  conversation_id?: string;
  payload: EventPayload;
}

export type EventType =
  // Chat & Cognition Events
  | "chat.message"
  | "thinking.start"
  | "thinking.end"
  // Progress & Planning Events
  | "progress.init"
  | "progress.update"
  | "progress.transition"
  // Filesystem Events
  | "fs.create"
  | "fs.write"
  | "fs.delete"
  // Edit Timeline Events
  | "edit.read"
  | "edit.start"
  | "edit.end"
  | "edit.security_check"
  // Build, Preview & Logs Events (Backend-owned)
  | "build.start"
  | "build.log"
  | "build.error"
  | "preview.ready"
  // Version & Deployment Events (Backend-owned)
  | "version.created"
  | "version.deployed"
  // Suggestions & User Interaction Events
  | "suggestion"
  | "ui.multiselect"
  // Error Events
  | "error"
  // Stream Lifecycle Events
  | "stream.complete"
  | "stream.await_input"
  | "stream.failed";

export type EventPayload =
  | ChatMessagePayload
  | ThinkingStartPayload
  | ThinkingEndPayload
  | ProgressInitPayload
  | ProgressUpdatePayload
  | ProgressTransitionPayload
  | FilesystemCreatePayload
  | FilesystemWritePayload
  | FilesystemDeletePayload
  | EditReadPayload
  | EditStartPayload
  | EditEndPayload
  | EditSecurityCheckPayload
  | BuildStartPayload
  | BuildLogPayload
  | BuildErrorPayload
  | PreviewReadyPayload
  | VersionCreatedPayload
  | VersionDeployedPayload
  | SuggestionPayload
  | UIMultiselectPayload
  | ErrorPayload
  | StreamCompletePayload
  | StreamAwaitInputPayload
  | StreamFailedPayload;

// ============================================================================
// Chat & Cognition Events
// ============================================================================

export interface ChatMessagePayload {
  content: string;
}

export interface ThinkingStartPayload {
  // Empty payload
}

export interface ThinkingEndPayload {
  duration_ms: number;
}

// ============================================================================
// Progress & Planning Events
// ============================================================================

export type ProgressMode = "modal" | "inline";
export type ProgressStepStatus = "pending" | "in_progress" | "completed" | "failed";

export interface ProgressStep {
  id: string;
  label: string;
  status: ProgressStepStatus;
}

export interface ProgressInitPayload {
  mode: ProgressMode;
  steps: ProgressStep[];
}

export interface ProgressUpdatePayload {
  step_id: string;
  status: ProgressStepStatus;
}

export interface ProgressTransitionPayload {
  mode: ProgressMode;
}

// ============================================================================
// Filesystem Events
// ============================================================================

export type FilesystemKind = "file" | "folder";

export interface FilesystemCreatePayload {
  path: string;
  kind: FilesystemKind;
}

export interface FilesystemWritePayload {
  path: string;
  kind: FilesystemKind;
  language?: string;
  content?: string;
}

export interface FilesystemDeletePayload {
  path: string;
}

// ============================================================================
// Edit Timeline Events
// ============================================================================

export interface EditReadPayload {
  path: string;
}

export interface EditStartPayload {
  path: string;
  content: string;
}

export interface EditEndPayload {
  path: string;
  duration_ms: number;
}

export type SecurityCheckStatus = "passed" | "failed";

export interface EditSecurityCheckPayload {
  path: string;
  status: SecurityCheckStatus;
}

// ============================================================================
// Build, Preview & Logs Events (Backend-owned)
// ============================================================================

export interface BuildStartPayload {
  container_id: string;
}

export type BuildLogLevel = "info" | "warning" | "error" | "debug";

export interface BuildLogPayload {
  level: BuildLogLevel;
  message: string;
}

export interface BuildErrorPayload {
  message: string;
  details?: string;
}

export interface PreviewReadyPayload {
  url: string;
  port?: number;
}

// ============================================================================
// Version & Deployment Events (Backend-owned)
// ============================================================================

export type VersionStatus = "stable" | "unstable" | "draft";

export interface VersionCreatedPayload {
  version_id: string;
  label: string;
  status: VersionStatus;
}

export type DeploymentEnvironment = "production" | "staging" | "development";

export interface VersionDeployedPayload {
  version_id: string;
  environment: DeploymentEnvironment;
}

// ============================================================================
// Suggestions & User Interaction Events
// ============================================================================

export interface SuggestionPayload {
  id: string;
  label: string;
  options: string[];
}

export interface UIMultiselectOption {
  id: string;
  label: string;
}

export interface UIMultiselectPayload {
  id: string;
  title: string;
  options: UIMultiselectOption[];
}

// ============================================================================
// Error Events
// ============================================================================

export type ErrorScope = "runtime" | "llm" | "validation" | "build";
export type ErrorAction = "retry" | "ask_user" | "auto_fix";

export interface ErrorPayload {
  scope: ErrorScope;
  message: string;
  details?: string;
  actions?: ErrorAction[];
}

// ============================================================================
// Stream Lifecycle Events
// ============================================================================

export interface StreamCompletePayload {
  // Empty payload
}

export type StreamAwaitInputReason = "suggestion" | "multiselect";

export interface StreamAwaitInputPayload {
  reason: StreamAwaitInputReason;
}

export interface StreamFailedPayload {
  // Empty payload
}

// ============================================================================
// Type Guards (for runtime type checking)
// ============================================================================

export function isChatMessageEvent(event: EventEnvelope): event is EventEnvelope & { payload: ChatMessagePayload } {
  return event.event_type === "chat.message";
}

export function isThinkingStartEvent(event: EventEnvelope): event is EventEnvelope & { payload: ThinkingStartPayload } {
  return event.event_type === "thinking.start";
}

export function isThinkingEndEvent(event: EventEnvelope): event is EventEnvelope & { payload: ThinkingEndPayload } {
  return event.event_type === "thinking.end";
}

export function isProgressInitEvent(event: EventEnvelope): event is EventEnvelope & { payload: ProgressInitPayload } {
  return event.event_type === "progress.init";
}

export function isProgressUpdateEvent(event: EventEnvelope): event is EventEnvelope & { payload: ProgressUpdatePayload } {
  return event.event_type === "progress.update";
}

export function isProgressTransitionEvent(event: EventEnvelope): event is EventEnvelope & { payload: ProgressTransitionPayload } {
  return event.event_type === "progress.transition";
}

export function isFilesystemCreateEvent(event: EventEnvelope): event is EventEnvelope & { payload: FilesystemCreatePayload } {
  return event.event_type === "fs.create";
}

export function isFilesystemWriteEvent(event: EventEnvelope): event is EventEnvelope & { payload: FilesystemWritePayload } {
  return event.event_type === "fs.write";
}

export function isFilesystemDeleteEvent(event: EventEnvelope): event is EventEnvelope & { payload: FilesystemDeletePayload } {
  return event.event_type === "fs.delete";
}

export function isEditReadEvent(event: EventEnvelope): event is EventEnvelope & { payload: EditReadPayload } {
  return event.event_type === "edit.read";
}

export function isEditStartEvent(event: EventEnvelope): event is EventEnvelope & { payload: EditStartPayload } {
  return event.event_type === "edit.start";
}

export function isEditEndEvent(event: EventEnvelope): event is EventEnvelope & { payload: EditEndPayload } {
  return event.event_type === "edit.end";
}

export function isEditSecurityCheckEvent(event: EventEnvelope): event is EventEnvelope & { payload: EditSecurityCheckPayload } {
  return event.event_type === "edit.security_check";
}

export function isBuildStartEvent(event: EventEnvelope): event is EventEnvelope & { payload: BuildStartPayload } {
  return event.event_type === "build.start";
}

export function isBuildLogEvent(event: EventEnvelope): event is EventEnvelope & { payload: BuildLogPayload } {
  return event.event_type === "build.log";
}

export function isBuildErrorEvent(event: EventEnvelope): event is EventEnvelope & { payload: BuildErrorPayload } {
  return event.event_type === "build.error";
}

export function isPreviewReadyEvent(event: EventEnvelope): event is EventEnvelope & { payload: PreviewReadyPayload } {
  return event.event_type === "preview.ready";
}

export function isVersionCreatedEvent(event: EventEnvelope): event is EventEnvelope & { payload: VersionCreatedPayload } {
  return event.event_type === "version.created";
}

export function isVersionDeployedEvent(event: EventEnvelope): event is EventEnvelope & { payload: VersionDeployedPayload } {
  return event.event_type === "version.deployed";
}

export function isSuggestionEvent(event: EventEnvelope): event is EventEnvelope & { payload: SuggestionPayload } {
  return event.event_type === "suggestion";
}

export function isUIMultiselectEvent(event: EventEnvelope): event is EventEnvelope & { payload: UIMultiselectPayload } {
  return event.event_type === "ui.multiselect";
}

export function isErrorEvent(event: EventEnvelope): event is EventEnvelope & { payload: ErrorPayload } {
  return event.event_type === "error";
}

export function isStreamCompleteEvent(event: EventEnvelope): event is EventEnvelope & { payload: StreamCompletePayload } {
  return event.event_type === "stream.complete";
}

export function isStreamAwaitInputEvent(event: EventEnvelope): event is EventEnvelope & { payload: StreamAwaitInputPayload } {
  return event.event_type === "stream.await_input";
}

export function isStreamFailedEvent(event: EventEnvelope): event is EventEnvelope & { payload: StreamFailedPayload } {
  return event.event_type === "stream.failed";
}

// ============================================================================
// Terminal Events (events that stop the stream and allow user input)
// ============================================================================

export function isTerminalEvent(event: EventEnvelope): boolean {
  return (
    event.event_type === "stream.complete" ||
    event.event_type === "stream.await_input" ||
    event.event_type === "stream.failed"
  );
}


