# api.py
import os
import json
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import AsyncGenerator
import asyncio
from utils.logger import log
from utils.event_logger import get_event_logger
from intent.greeting_generator import generate_greeting_response
from events import EventEmitter
from events.event_types import EventEnvelope

# Import from unified_client for multi-family support
from models.unified_client import (
    generate_text,
    generate_stream,
    classify_intent,
    classify_page_type,
    analyze_query_detail,
    chat_response,
    parse_project_json,
    save_project_files,
    classify_modification_complexity,
    get_model_for_complexity,
    get_smaller_model,
    generate_feature_recommendations,
)
from data.page_types_reference import get_page_type_by_key, search_page_type_by_keywords
from data.questionnaire_config import get_questionnaire, has_questionnaire
from data.page_categories import get_all_categories, get_category_key_from_display_name

# --------------------------------------------------
# ENV + DIRS
# --------------------------------------------------
load_dotenv()

OUTPUT_DIR = "output"
MODIFIED_DIR = "modified_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODIFIED_DIR, exist_ok=True)

THEMES = ["Light", "Dark", "Minimal"]

# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------
app = FastAPI(
    title="Webpage Builder AI API",
    description="API for generating and modifying web projects using AI",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (in production, use Redis or database)
sessions: Dict[str, Dict[str, Any]] = {}

# --------------------------------------------------
# REQUEST/RESPONSE MODELS
# --------------------------------------------------

class IntentRequest(BaseModel):
    user_input: str = Field(..., description="User query or input")

class IntentResponse(BaseModel):
    label: str
    meta: Dict[str, Any]
    greeting_response: Optional[str] = None
    chat_response: Optional[str] = None
    page_type_key: Optional[str] = None
    page_type_meta: Optional[Dict[str, Any]] = None
    needs_questionnaire: Optional[bool] = None
    needs_page_type_selection: Optional[bool] = None

class PageTypeRequest(BaseModel):
    page_type_key: str = Field(..., description="Selected page type key")

class QuestionnaireAnswer(BaseModel):
    question_id: str
    answer: Any  # Can be string or list

class QuestionnaireRequest(BaseModel):
    page_type_key: str
    answers: List[QuestionnaireAnswer]

class WizardInputs(BaseModel):
    hero_text: Optional[str] = None
    subtext: Optional[str] = None
    cta: Optional[str] = "Get Started"
    theme: Optional[str] = "Light"

class GenerateProjectRequest(BaseModel):
    session_id: str
    wizard_inputs: WizardInputs
    model_family: str = Field(default="gemini", description="Model family: 'gemini', 'gpt', or 'claude'")
    page_type_key: Optional[str] = None
    questionnaire_answers: Optional[Dict[str, Any]] = None

class ModifyProjectRequest(BaseModel):
    session_id: str
    instruction: str
    model_family: str = Field(default="gemini", description="Model family: 'gemini', 'gpt', or 'claude'")
    base_project_path: Optional[str] = None

class ProjectResponse(BaseModel):
    success: bool
    project_path: Optional[str] = None
    project_json_path: Optional[str] = None
    files_count: Optional[int] = None
    message: str
    events_file: Optional[str] = None

# Message endpoint models (for POST /stream/message/)
class QuestionResponseContent(BaseModel):
    """Content for question response - varies by question type"""
    label: str
    answer: Optional[str] = None  # For open_ended
    selectedOption: Optional[str] = None  # For mcq
    selectedOptions: Optional[List[str]] = None  # For multi_select
    answers: Optional[List[Dict[str, Any]]] = None  # For form: [{"label": str, "answer": str | List[str]}]

class QuestionResponse(BaseModel):
    """Single question response"""
    q_id: str
    q_type: str = Field(..., description="Question type: 'open_ended', 'mcq', 'multi_select', or 'form'")
    content: QuestionResponseContent
    skipped: bool = False

class MessageRequest(BaseModel):
    """Request model for POST /stream/message/ endpoint"""
    project_id: str = Field(..., description="Project identifier (required)")
    chat_id: str = Field(..., description="Chat/conversation identifier (required, used to load context)")
    responses: List[QuestionResponse] = Field(..., description="Array of question responses (required)")
    user_input: Optional[str] = Field(None, description="Optional additional text input from chat textarea")

class MessageResponse(BaseModel):
    """Response model for POST /stream/message/ endpoint"""
    status: str
    message: str

# Unified streaming request model
class StreamRequest(BaseModel):
    """Unified request model for streaming API - action is inferred from payload"""
    session_id: Optional[str] = Field(None, description="Session identifier (optional, auto-generated if not provided)")
    model_family: str = Field(default="gemini", description="Model family: 'gemini', 'gpt', or 'claude'")
    user_input: Optional[str] = Field(None, description="User input/query. For project generation: required on first call")
    page_type_key: Optional[str] = Field(None, description="Page type key. For project generation: optional on first call (will be determined), required on follow-up")
    questionnaire_answers: Optional[Dict[str, Any]] = Field(None, description="Questionnaire answers. For project generation: optional, provided after questions are asked")
    wizard_inputs: Optional[WizardInputs] = Field(None, description="Wizard inputs for project generation")
    instruction: Optional[str] = Field(None, description="Modification instruction (indicates modify_project action)")
    base_project_path: Optional[str] = Field(None, description="Base project path for modifications")
    project_id: Optional[str] = Field(None, description="Project identifier (optional, auto-generated if not provided)")

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def get_latest_project():
    """
    Priority:
    1. latest modified_output/project_x/project.json
    2. output/project.json
    """
    if os.path.exists(MODIFIED_DIR):
        versions = sorted(
            d for d in os.listdir(MODIFIED_DIR) if d.startswith("project_")
        )
        if versions:
            path = os.path.join(MODIFIED_DIR, versions[-1], "project.json")
            with open(path) as f:
                return path, json.load(f)["project"]

    base = os.path.join(OUTPUT_DIR, "project.json")
    if os.path.exists(base):
        with open(base) as f:
            return base, json.load(f)["project"]

    return None, None


def safe_theme_index(value):
    v = (value or "Light").strip().title()
    return THEMES.index(v) if v in THEMES else 0


def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Get or create a session"""
    if session_id not in sessions:
        sessions[session_id] = {
            "step": 0,
            "collected": {},
            "initial_intent": "",
            "final_summary": "",
            "last_project_path": "",
            "last_output_text": "",
            "page_type_key": "",
            "page_type_config": None,
            "needs_questionnaire": False,
            "questionnaire_answers": {},
            "selected_page_category": None,
            "questionnaire_emitter": None,
            "must_have_features": {},
            "competitor_suggestions": {},
            "history": {
                "initial_query": "",
                "wizard_inputs": {},
                "modifications": [],
            }
        }
    return sessions[session_id]


def _next_chunk(gen):
    """Helper to get next chunk from generator"""
    try:
        return next(gen)
    except StopIteration:
        return None


def generate_short_q_id() -> str:
    """Generate a 4-digit unique identifier for question IDs (q_xxxx)"""
    unique_id = uuid.uuid4().hex[:4]
    return f"q_{unique_id}"

# --------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Webpage Builder AI API",
        "version": "1.0.0",
        "endpoints": {
            "stream": "POST /api/v1/stream - Unified streaming endpoint for all LLM interactions",
            "get_page_types": "GET /api/v1/page-types",
            "get_questionnaire": "GET /api/v1/questionnaire/{page_type_key}",
            "get_latest_project": "GET /api/v1/latest-project",
        }
    }


async def stream_events(request: StreamRequest) -> AsyncGenerator[str, None]:
    """Unified streaming function that handles all LLM interactions - action is inferred from payload"""
    # Auto-generate session_id if not provided
    session_id = request.session_id or f"session_{int(time.time())}"
    session = get_or_create_session(session_id)
    
    # Get model family from request (default to gemini for backward compatibility)
    model_family = request.model_family.lower().strip() if request.model_family else "gemini"
    
    # Infer action from payload
    # Priority: instruction -> modify, user_input with page_type -> generate, user_input only -> classify/generate, else error
    if request.instruction:
        action = "modify_project"
    elif request.user_input:
        if request.page_type_key or request.questionnaire_answers or request.wizard_inputs:
            action = "generate_project"
        else:
            # Just user_input - could be classify_intent or chat, we'll determine in classify_intent flow
            action = "classify_intent"
    elif request.page_type_key or request.questionnaire_answers or request.wizard_inputs:
        action = "generate_project"
    else:
        yield yield_error("validation", "Invalid request: must provide user_input, instruction, or page_type_key/questionnaire_answers")
        await asyncio.sleep(0)
        return
    
    # Initialize event system
    event_logger = get_event_logger()
    project_id = f"proj_{int(time.time())}"
    conversation_id = f"conv_{int(time.time())}"
    emitter = EventEmitter(
        project_id=project_id,
        conversation_id=conversation_id,
        callback=lambda event: event_logger.log_event(event)
    )
    
    # Helper function to yield events in proper SSE format
    def yield_event(event: EventEnvelope):
        """Yield an event in proper SSE format according to contract"""
        return f"data: {event.to_json()}\n\n"
    
    # Helper to create and yield error event
    def yield_error(scope: str, message: str, details: Optional[str] = None):
        """Create and yield an error event"""
        from events import ErrorEvent
        error_event = ErrorEvent.create(
            scope=scope,
            message=message,
            details=details,
            project_id=project_id,
            conversation_id=conversation_id
        )
        return yield_event(error_event)
    
    try:
        if action == "classify_intent":
            if not request.user_input:
                yield yield_error("validation", "user_input is required for classify_intent")
                await asyncio.sleep(0)
                return
            
            user_input = request.user_input.strip()
            chat_event = emitter.emit_chat_message(f"Analyzing your request: {user_input} (using {model_family})")
            yield yield_event(chat_event)
            await asyncio.sleep(0)
            
            # Stream intent classification with model_family
            thinking_start = emitter.emit_thinking_start()
            yield yield_event(thinking_start)
            await asyncio.sleep(0)
            
            label, meta = classify_intent(user_input, model_family=model_family)
            
            thinking_end = emitter.emit_thinking_end(duration_ms=1000)
            yield yield_event(thinking_end)
            await asyncio.sleep(0)
            
            # Emit classification result as chat message (contract doesn't have intent_classified event)
            result_msg = f"Intent: {label} (confidence: {meta.get('confidence', 0):.2f})"
            result_event = emitter.emit_chat_message(result_msg)
            yield yield_event(result_event)
            await asyncio.sleep(0)
            
            if label == "greeting_only":
                greeting = generate_greeting_response(user_input)
                greeting_event = emitter.emit_chat_message(greeting)
                yield yield_event(greeting_event)
                await asyncio.sleep(0)
                complete_event = emitter.emit_stream_complete()
                yield yield_event(complete_event)
                await asyncio.sleep(0)
                return
            
            if label == "illegal":
                illegal_event = emitter.emit_chat_message("Sorry — I can't help with that request.")
                yield yield_event(illegal_event)
                await asyncio.sleep(0)
                yield yield_error("llm", "Illegal request")
                await asyncio.sleep(0)
                complete_event = emitter.emit_stream_complete()
                yield yield_event(complete_event)
                await asyncio.sleep(0)
                return
            
            if label == "chat":
                smaller_model = get_smaller_model(model_family=model_family)
                help_event = emitter.emit_chat_message("Let me help you with that...")
                yield yield_event(help_event)
                await asyncio.sleep(0)
                
                thinking_start = emitter.emit_thinking_start()
                yield yield_event(thinking_start)
                await asyncio.sleep(0)
                
                # Stream chat response - use edit.start for streaming chunks (contract allows multiple chunks)
                from events import EditStartEvent, EditEndEvent
                response_text = ""
                loop = asyncio.get_event_loop()
                stream_gen = generate_stream(user_input, model=smaller_model, model_family=model_family)
                
                edit_start_time = time.time()
                while True:
                    chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
                    if chunk is None:
                        break
                    response_text += chunk
                    # Use edit.start for streaming chunks (can be emitted multiple times per contract)
                    edit_chunk = EditStartEvent.create(
                        path="chat_response",
                        content=chunk,
                        project_id=project_id,
                        conversation_id=conversation_id
                    )
                    yield yield_event(edit_chunk)
                    await asyncio.sleep(0)
                
                # Emit edit.end after streaming completes (per contract)
                edit_duration_ms = int((time.time() - edit_start_time) * 1000)
                edit_end = EditEndEvent.create(
                    path="chat_response",
                    duration_ms=edit_duration_ms,
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                yield yield_event(edit_end)
                await asyncio.sleep(0.01)
                log(f"[STREAM] ✓ edit.end emitted: path=chat_response, duration={edit_duration_ms}ms")
                
                thinking_end = emitter.emit_thinking_end(duration_ms=1000)
                yield yield_event(thinking_end)
                await asyncio.sleep(0)
                
                # Emit final chat message with complete response
                final_event = emitter.emit_chat_message(response_text)
                yield yield_event(final_event)
                await asyncio.sleep(0)
                
                complete_event = emitter.emit_stream_complete()
                yield yield_event(complete_event)
                await asyncio.sleep(0)
                return
            
            if label == "webpage_build":
                # Classify page type with model_family
                page_type_msg = emitter.emit_chat_message("Determining the best page type for your project...")
                yield yield_event(page_type_msg)
                await asyncio.sleep(0)
                
                thinking_start = emitter.emit_thinking_start()
                yield yield_event(thinking_start)
                await asyncio.sleep(0)
                
                page_type_key, page_type_meta = classify_page_type(user_input, model_family=model_family)
                
                thinking_end = emitter.emit_thinking_end(duration_ms=1000)
                yield yield_event(thinking_end)
                await asyncio.sleep(0)
                
                # Emit page type result as chat message
                page_result_msg = f"Selected page type: {page_type_key}"
                page_result_event = emitter.emit_chat_message(page_result_msg)
                yield yield_event(page_result_event)
                await asyncio.sleep(0)
                
                # Analyze query detail with model_family
                needs_followup, detail_confidence = analyze_query_detail(user_input, model_family=model_family)
                
                session["page_type_key"] = page_type_key
                session["initial_intent"] = user_input
                
                page_type_config = get_page_type_by_key(page_type_key)
                session["page_type_config"] = page_type_config
                
                if page_type_key == "generic":
                    # Need page type selection - use chat.question event (contract-compliant)
                    gather_msg = emitter.emit_chat_message("I need to know what type of page you want to build.")
                    yield yield_event(gather_msg)
                    await asyncio.sleep(0)
                    
                    categories = get_all_categories()
                    # Convert categories to chat.question format (multi_select)
                    question_options = [{"id": key, "label": cat["display_name"]} for key, cat in categories.items()]
                    
                    # Generate unique q_id using 4-digit UUID
                    q_id = generate_short_q_id()
                    
                    # Store question options in session for later mapping
                    session[f"question_options_{q_id}"] = question_options
                    
                    question_event = emitter.emit_chat_question(
                        q_id=q_id,
                        question_type="multi_select",
                        label="Please select a page type",
                        is_skippable=False,
                        content={"options": question_options}
                    )
                    yield yield_event(question_event)
                    await asyncio.sleep(0)
                    
                    await_input = emitter.emit_stream_await_input(reason="suggestion")
                    yield yield_event(await_input)
                    await asyncio.sleep(0)
                    return
                
                if needs_followup and has_questionnaire(page_type_key):
                    # Need questionnaire
                    questionnaire = get_questionnaire(page_type_key)
                    gather_msg = emitter.emit_chat_message("I need to gather some additional information to create the perfect page for you.")
                    yield yield_event(gather_msg)
                    
                    # Emit questions using chat.question events (contract-compliant)
                    type_mapping = {"radio": "mcq", "multiselect": "multi_select"}
                    for question_data in questionnaire["questions"]:
                        # Generate unique q_id using 4-digit UUID (scalable)
                        q_id = generate_short_q_id()
                        q_text = question_data["question"]
                        q_type = question_data["type"]
                        options = question_data.get("options", [])
                        
                        contract_type = type_mapping.get(q_type, "open_ended")
                        content = {}
                        if contract_type in ["mcq", "multi_select"]:
                            content["options"] = options
                            # Store question options in session for later mapping
                            session[f"question_options_{q_id}"] = options
                        
                        question_event = emitter.emit_chat_question(
                            q_id=q_id,
                            question_type=contract_type,
                            label=q_text,
                            is_skippable=False,
                            content=content
                        )
                        yield yield_event(question_event)
                        await asyncio.sleep(0)
                    
                    await_input = emitter.emit_stream_await_input(reason="suggestion")
                    yield yield_event(await_input)
                    await asyncio.sleep(0)
                    return
                
                # Ready to generate - emit as chat message
                ready_msg = emitter.emit_chat_message(f"Ready to generate {page_type_key} project")
                yield yield_event(ready_msg)
                await asyncio.sleep(0)
                complete_event = emitter.emit_stream_complete()
                yield yield_event(complete_event)
                await asyncio.sleep(0)
                return
        
        elif action == "generate_project":
            # Check if this is first-time request (with user_input) or follow-up (with page_type_key)
            user_input = request.user_input
            page_type_key = request.page_type_key or session.get("page_type_key")
            questionnaire_answers = request.questionnaire_answers or session.get("questionnaire_answers", {})
            wizard_inputs = request.wizard_inputs or WizardInputs()
            
            # If user_input is provided but no page_type_key, do classification flow first
            if user_input and not page_type_key:
                # This is the first request - classify intent and page type
                user_input = user_input.strip()
                analyze_msg = emitter.emit_chat_message(f"Analyzing your request: {user_input} (using {model_family})")
                yield yield_event(analyze_msg)
                await asyncio.sleep(0)
                
                # Classify intent
                thinking_start = emitter.emit_thinking_start()
                yield yield_event(thinking_start)
                await asyncio.sleep(0)
                
                label, meta = classify_intent(user_input, model_family=model_family)
                
                thinking_end = emitter.emit_thinking_end(duration_ms=1000)
                yield yield_event(thinking_end)
                await asyncio.sleep(0)
                
                if label != "webpage_build":
                    if label == "greeting_only":
                        greeting = generate_greeting_response(user_input)
                        greeting_event = emitter.emit_chat_message(greeting)
                        yield yield_event(greeting_event)
                        await asyncio.sleep(0)
                    elif label == "illegal":
                        illegal_event = emitter.emit_chat_message("Sorry — I can't help with that request.")
                        yield yield_event(illegal_event)
                        await asyncio.sleep(0)
                        yield yield_error("llm", "Illegal request")
                        await asyncio.sleep(0)
                    elif label == "chat":
                        # Handle chat response
                        smaller_model = get_smaller_model(model_family=model_family)
                        help_msg = emitter.emit_chat_message("Let me help you with that...")
                        yield yield_event(help_msg)
                        await asyncio.sleep(0)
                        
                        thinking_start = emitter.emit_thinking_start()
                        yield yield_event(thinking_start)
                        await asyncio.sleep(0)
                        
                        from events import EditStartEvent, EditEndEvent
                        response_text = ""
                        loop = asyncio.get_event_loop()
                        stream_gen = generate_stream(user_input, model=smaller_model, model_family=model_family)
                        
                        edit_start_time = time.time()
                        while True:
                            chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
                            if chunk is None:
                                break
                            response_text += chunk
                            edit_chunk = EditStartEvent.create(
                                path="chat_response",
                                content=chunk,
                                project_id=project_id,
                                conversation_id=conversation_id
                            )
                            yield yield_event(edit_chunk)
                            await asyncio.sleep(0)
                        
                        # Emit edit.end after streaming completes (per contract)
                        edit_duration_ms = int((time.time() - edit_start_time) * 1000)
                        edit_end = EditEndEvent.create(
                            path="chat_response",
                            duration_ms=edit_duration_ms,
                            project_id=project_id,
                            conversation_id=conversation_id
                        )
                        yield yield_event(edit_end)
                        await asyncio.sleep(0)
                        
                        thinking_end = emitter.emit_thinking_end(duration_ms=1000)
                        yield yield_event(thinking_end)
                        await asyncio.sleep(0)
                        
                        final_msg = emitter.emit_chat_message(response_text)
                        yield yield_event(final_msg)
                        await asyncio.sleep(0)
                    
                    complete_event = emitter.emit_stream_complete()
                    yield yield_event(complete_event)
                    await asyncio.sleep(0)
                    return
                
                # Intent is webpage_build - classify page type
                page_type_msg = emitter.emit_chat_message("Determining the best page type for your project...")
                yield yield_event(page_type_msg)
                await asyncio.sleep(0)
                
                thinking_start = emitter.emit_thinking_start()
                yield yield_event(thinking_start)
                await asyncio.sleep(0)
                
                page_type_key, page_type_meta = classify_page_type(user_input, model_family=model_family)
                
                thinking_end = emitter.emit_thinking_end(duration_ms=1000)
                yield yield_event(thinking_end)
                await asyncio.sleep(0)
                
                # Store in session
                session["page_type_key"] = page_type_key
                session["initial_intent"] = user_input
                
                page_type_config = get_page_type_by_key(page_type_key)
                session["page_type_config"] = page_type_config
                
                # Emit page type result
                page_result_msg = f"Selected page type: {page_type_key}"
                page_result_event = emitter.emit_chat_message(page_result_msg)
                yield yield_event(page_result_event)
                await asyncio.sleep(0)
                
                # Analyze if questionnaire is needed
                needs_followup, detail_confidence = analyze_query_detail(user_input, model_family=model_family)
                
                if page_type_key == "generic":
                    # Need page type selection - use chat.question event (contract-compliant)
                    gather_msg = emitter.emit_chat_message("I need to know what type of page you want to build.")
                    yield yield_event(gather_msg)
                    await asyncio.sleep(0)
                    
                    categories = get_all_categories()
                    # Convert categories to chat.question format (multi_select)
                    question_options = [{"id": key, "label": cat["display_name"]} for key, cat in categories.items()]
                    
                    # Generate unique q_id using 4-digit UUID
                    q_id = generate_short_q_id()
                    
                    # Store question options in session for later mapping
                    session[f"question_options_{q_id}"] = question_options
                    
                    question_event = emitter.emit_chat_question(
                        q_id=q_id,
                        question_type="multi_select",
                        label="Please select a page type",
                        is_skippable=False,
                        content={"options": question_options}
                    )
                    yield yield_event(question_event)
                    await asyncio.sleep(0)
                    
                    await_input = emitter.emit_stream_await_input(reason="suggestion")
                    yield yield_event(await_input)
                    await asyncio.sleep(0)
                    return
                
                if needs_followup and has_questionnaire(page_type_key):
                    # Need questionnaire
                    questionnaire = get_questionnaire(page_type_key)
                    gather_msg = emitter.emit_chat_message("I need to gather some additional information to create the perfect page for you.")
                    yield yield_event(gather_msg)
                    await asyncio.sleep(0)
                    
                    # Emit questions
                    type_mapping = {"radio": "mcq", "multiselect": "multi_select"}
                    for question_data in questionnaire["questions"]:
                        # Generate unique q_id using 4-digit UUID (scalable)
                        q_id = generate_short_q_id()
                        q_text = question_data["question"]
                        q_type = question_data["type"]
                        options = question_data.get("options", [])
                        
                        contract_type = type_mapping.get(q_type, "open_ended")
                        content = {}
                        if contract_type in ["mcq", "multi_select"]:
                            content["options"] = options
                            # Store question options in session for later mapping
                            session[f"question_options_{q_id}"] = options
                        
                        question_event = emitter.emit_chat_question(
                            q_id=q_id,
                            question_type=contract_type,
                            label=q_text,
                            is_skippable=False,
                            content=content
                        )
                        yield yield_event(question_event)
                        await asyncio.sleep(0)
                    
                    await_input = emitter.emit_stream_await_input(reason="suggestion")
                    yield yield_event(await_input)
                    await asyncio.sleep(0)
                    return
                
                # Ready to generate - continue to generation below
            
            # Now proceed with project generation
            if not page_type_key:
                yield yield_error("validation", "page_type_key is required. Please provide user_input first or select a page type.")
                await asyncio.sleep(0)
                return
            
            start_msg = emitter.emit_chat_message("Starting project generation...")
            yield yield_event(start_msg)
            await asyncio.sleep(0)
            
            # Build prompt
            base_prompt = (
                "Return JSON only: React+Vite+TypeScript project. Schema: {\"project\": {\"name\": string, \"description\": string, \"files\": {...}, \"dirents\": {...}, \"meta\": {...}}}. Files: strings or {\"content\": \"...\"}.\n\n"
                "🚨 REACT APP ONLY - NO STATIC HTML 🚨\n\n"
                "REQUIRED:\n"
                "1. React 18+ + TypeScript (.tsx only, NO .html pages)\n"
                "2. Vite + @vitejs/plugin-react\n"
                "3. Structure: src/main.tsx, src/App.tsx (React Router), src/pages/*.tsx, src/components/*.tsx, src/types/*.ts\n"
                "4. package.json: React, React-DOM, Vite, TypeScript, react-router-dom\n"
                "5. React Router: BrowserRouter, Routes, Route\n"
                "6. Functional components + TypeScript interfaces\n"
                "7. React hooks: useState, useEffect, useContext\n"
                "8. Interactive: buttons/forms/nav work\n"
                "9. Styling: CSS Modules/styled-components/Tailwind (NOT inline HTML styles)\n"
                "10. index.html = entry only, all content via React\n\n"
                "FORBIDDEN: Static HTML pages, plain HTML/CSS, image-only layouts, missing Router/TypeScript.\n"
            )
            
            if page_type_key:
                page_type_config = get_page_type_by_key(page_type_key)
                if page_type_config:
                    base_prompt += f"\n=== PAGE TYPE: {page_type_config['name']} ({page_type_config['category']}) ===\n"
                    base_prompt += f"Target User: {page_type_config['end_user']}\n\n"
                    base_prompt += "REQUIRED CORE PAGES:\n"
                    for i, page in enumerate(page_type_config['core_pages'], 1):
                        base_prompt += f"{i}. {page}\n"
                    base_prompt += "\n\nREQUIRED COMPONENTS TO IMPLEMENT:\n"
                    for i, component in enumerate(page_type_config['components'], 1):
                        base_prompt += f"{i}. **{component['name']}**: {component['description']}\n"
            
            if questionnaire_answers:
                base_prompt += "\n=== USER REQUIREMENTS (from questionnaire) ===\n"
                for key, value in questionnaire_answers.items():
                    if isinstance(value, list):
                        base_prompt += f"- {key}\n  Selected: {', '.join(value)}\n"
                    else:
                        base_prompt += f"- {key}\n  Answer: {value}\n"
            
            wizard_data = wizard_inputs.dict()
            final_prompt = base_prompt + "USER_FIELDS:\n" + json.dumps(wizard_data, ensure_ascii=False)
            
            # Get default model for the specified family
            from models.model_factory import get_provider
            try:
                provider = get_provider(model_family)
                webpage_model = provider.get_default_model()
            except Exception as e:
                yield yield_error("llm", f"Failed to initialize {model_family} provider: {str(e)}")
                await asyncio.sleep(0)
                return
            
            progress_init = emitter.emit_progress_init(
                steps=[
                    {"id": "prepare", "label": "Preparing", "status": "in_progress"},
                    {"id": "generate", "label": "Generating", "status": "pending"},
                    {"id": "parse", "label": "Parsing", "status": "pending"},
                    {"id": "save", "label": "Saving", "status": "pending"},
                ],
                mode="inline"
            )
            yield yield_event(progress_init)
            await asyncio.sleep(0)
            
            progress_prepare = emitter.emit_progress_update("prepare", "completed")
            yield yield_event(progress_prepare)
            await asyncio.sleep(0)
            
            progress_generate = emitter.emit_progress_update("generate", "in_progress")
            yield yield_event(progress_generate)
            await asyncio.sleep(0)
            
            thinking_start = emitter.emit_thinking_start()
            yield yield_event(thinking_start)
            await asyncio.sleep(0)
            
            gen_msg = emitter.emit_chat_message(f"Generating project using {webpage_model} ({model_family})...")
            yield yield_event(gen_msg)
            await asyncio.sleep(0)
            start_time = time.time()
            
            # Stream the generation - use edit.start for streaming chunks
            from events import EditStartEvent, EditEndEvent
            output = ""
            loop = asyncio.get_event_loop()
            stream_gen = generate_stream(final_prompt, model=webpage_model, model_family=model_family)
            
            edit_start_time = time.time()
            while True:
                chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
                if chunk is None:
                    break
                output += chunk
                # Use edit.start for streaming generation chunks
                edit_chunk = EditStartEvent.create(
                    path="project_generation",
                    content=chunk,
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                yield yield_event(edit_chunk)
                await asyncio.sleep(0)
            
            # Emit edit.end after streaming completes (per contract)
            edit_duration_ms = int((time.time() - edit_start_time) * 1000)
            edit_end = EditEndEvent.create(
                path="project_generation",
                duration_ms=edit_duration_ms,
                project_id=project_id,
                conversation_id=conversation_id
            )
            yield yield_event(edit_end)
            await asyncio.sleep(0.01)
            log(f"[STREAM] ✓ edit.end emitted: path=project_generation, duration={edit_duration_ms}ms")
            
            elapsed_time = time.time() - start_time
            thinking_end = emitter.emit_thinking_end(duration_ms=int(elapsed_time * 1000))
            yield yield_event(thinking_end)
            await asyncio.sleep(0)
            
            progress_gen_complete = emitter.emit_progress_update("generate", "completed")
            yield yield_event(progress_gen_complete)
            await asyncio.sleep(0)
            
            progress_parse = emitter.emit_progress_update("parse", "in_progress")
            yield yield_event(progress_parse)
            await asyncio.sleep(0)
            
            if not output or len(output) < 100:
                raise Exception("Model returned empty or very short output")
            
            project = parse_project_json(output)
            
            if not project:
                parse_failed = emitter.emit_progress_update("parse", "failed")
                yield yield_event(parse_failed)
                await asyncio.sleep(0)
                
                error_event = emitter.emit_error(
                    scope="validation",
                    message="Failed to parse JSON from model output",
                    details="The model may have returned invalid JSON or non-JSON content.",
                    actions=["retry", "ask_user"]
                )
                yield yield_event(error_event)
                await asyncio.sleep(0)
                
                stream_failed = emitter.emit_stream_failed()
                yield yield_event(stream_failed)
                await asyncio.sleep(0)
                return
            
            parse_complete = emitter.emit_progress_update("parse", "completed")
            yield yield_event(parse_complete)
            await asyncio.sleep(0)
            
            save_progress = emitter.emit_progress_update("save", "in_progress")
            yield yield_event(save_progress)
            await asyncio.sleep(0)
            
            parsed_msg = emitter.emit_chat_message(f"JSON parsed successfully. Project has {len(project.get('files', {}))} files.")
            yield yield_event(parsed_msg)
            await asyncio.sleep(0)
            
            # Save project
            project_json_path = f"{OUTPUT_DIR}/project.json"
            with open(project_json_path, "w") as f:
                json.dump({"project": project}, f, indent=2)
            
            # Emit fs.write for project.json - MUST be streamed per contract (fs.write is single source of truth)
            fs_write_project = emitter.emit_fs_write(
                path="project.json",
                kind="file",
                language="json",
                content=json.dumps({"project": project}, indent=2)
            )
            yield yield_event(fs_write_project)
            await asyncio.sleep(0)
            
            # Save all files
            files = project.get('files', {})
            for file_path, file_content in files.items():
                if isinstance(file_content, dict):
                    content = file_content.get('content', '')
                    language = file_content.get('language', None)
                else:
                    content = file_content
                    language = None
                
                if not language:
                    if file_path.endswith('.tsx') or file_path.endswith('.ts'):
                        language = 'typescript'
                    elif file_path.endswith('.jsx') or file_path.endswith('.js'):
                        language = 'javascript'
                    elif file_path.endswith('.css'):
                        language = 'css'
                    elif file_path.endswith('.json'):
                        language = 'json'
                    elif file_path.endswith('.html'):
                        language = 'html'
                
                # Emit fs.write for each file - MUST be streamed per contract
                fs_write = emitter.emit_fs_write(
                    path=file_path,
                    kind="file",
                    language=language,
                    content=content if isinstance(content, str) else json.dumps(content)
                )
                yield yield_event(fs_write)
                await asyncio.sleep(0)
            
            save_project_files(project, f"{OUTPUT_DIR}/project")
            
            save_complete = emitter.emit_progress_update("save", "completed")
            yield yield_event(save_complete)
            await asyncio.sleep(0)
            
            success_msg = emitter.emit_chat_message("Base project generated successfully!")
            yield yield_event(success_msg)
            await asyncio.sleep(0)
            
            complete_event = emitter.emit_stream_complete()
            yield yield_event(complete_event)
            await asyncio.sleep(0)
            return
        
        elif action == "modify_project":
            if not request.instruction:
                yield yield_error("validation", "instruction is required for modify_project")
                await asyncio.sleep(0)
                return
            
            base_path = request.base_project_path or session.get("last_project_path")
            if not base_path:
                base_path, _ = get_latest_project()
            
            if not base_path or not os.path.exists(base_path):
                yield yield_error("validation", "Base project not found")
                await asyncio.sleep(0)
                return
            
            with open(base_path) as f:
                base_project = json.load(f)["project"]
            
            complexity, complexity_meta = classify_modification_complexity(request.instruction, model_family=model_family)
            mod_model = get_model_for_complexity(complexity, model_family=model_family)
            
            mod_prompt = f"""Modify project JSON. Return JSON only: {{"project": {{...}}}}. Match base schema. Change ONLY requested parts, keep rest unchanged. NO markdown/code blocks/explanations. Raw JSON only.

Base: {json.dumps({"project": base_project}, indent=2)}
Request: {request.instruction}"""
            
            mod_msg = emitter.emit_chat_message(f"Modifying project (complexity: {complexity})...")
            yield yield_event(mod_msg)
            await asyncio.sleep(0)
            
            thinking_start = emitter.emit_thinking_start()
            yield yield_event(thinking_start)
            await asyncio.sleep(0)
            
            # Stream modification - use edit.start for streaming chunks
            from events import EditStartEvent, EditEndEvent
            mod_out = ""
            loop = asyncio.get_event_loop()
            stream_gen = generate_stream(mod_prompt, model=mod_model, model_family=model_family)
            
            edit_start_time = time.time()
            while True:
                chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
                if chunk is None:
                    break
                mod_out += chunk
                # Use edit.start for streaming modification chunks
                edit_chunk = EditStartEvent.create(
                    path="project_modification",
                    content=chunk,
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                yield yield_event(edit_chunk)
                await asyncio.sleep(0)
            
            # Emit edit.end after streaming completes (per contract)
            edit_duration_ms = int((time.time() - edit_start_time) * 1000)
            edit_end = EditEndEvent.create(
                path="project_modification",
                duration_ms=edit_duration_ms,
                project_id=project_id,
                conversation_id=conversation_id
            )
            yield yield_event(edit_end)
            await asyncio.sleep(0.01)
            log(f"[STREAM] ✓ edit.end emitted: path=project_modification, duration={edit_duration_ms}ms")
            
            thinking_end = emitter.emit_thinking_end(duration_ms=1000)
            yield yield_event(thinking_end)
            await asyncio.sleep(0)
            
            mod_project = parse_project_json(mod_out)
            
            if not mod_project:
                # Retry with default model for the family
                from models.model_factory import get_provider
                provider = get_provider(model_family)
                default_model = provider.get_default_model()
                if mod_model != default_model:
                    mod_out = ""
                    stream_gen = generate_stream(mod_prompt, model=default_model, model_family=model_family)
                    edit_retry_start_time = time.time()
                    while True:
                        chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
                        if chunk is None:
                            break
                        mod_out += chunk
                        # Use edit.start for streaming modification chunks
                        edit_chunk = EditStartEvent.create(
                            path="project_modification",
                            content=chunk,
                            project_id=project_id,
                            conversation_id=conversation_id
                        )
                        yield yield_event(edit_chunk)
                        await asyncio.sleep(0)
                    
                    # Emit edit.end after retry streaming completes (per contract)
                    edit_retry_duration_ms = int((time.time() - edit_retry_start_time) * 1000)
                    edit_retry_end = EditEndEvent.create(
                        path="project_modification",
                        duration_ms=edit_retry_duration_ms,
                        project_id=project_id,
                        conversation_id=conversation_id
                    )
                    yield yield_event(edit_retry_end)
                    await asyncio.sleep(0.01)
                    log(f"[STREAM] ✓ edit.end emitted (retry): path=project_modification, duration={edit_retry_duration_ms}ms")
                    mod_project = parse_project_json(mod_out)
            
            if not mod_project:
                yield yield_error("validation", "Invalid modification output")
                await asyncio.sleep(0)
                return
            
            # Save modified project
            version = f"project_{int(time.time())}"
            dest = os.path.join(MODIFIED_DIR, version)
            os.makedirs(dest, exist_ok=True)
            
            project_json_path = os.path.join(dest, "project.json")
            with open(project_json_path, "w") as f:
                json.dump({"project": mod_project}, f, indent=2)
            
            save_project_files(mod_project, os.path.join(dest, "project"))
            
            session["last_project_path"] = project_json_path
            
            # Emit filesystem events for modified files
            files = mod_project.get('files', {})
            for file_path, file_content in files.items():
                if isinstance(file_content, dict):
                    content = file_content.get('content', '')
                    language = file_content.get('language', None)
                else:
                    content = file_content
                    language = None
                
                if not language:
                    if file_path.endswith('.tsx') or file_path.endswith('.ts'):
                        language = 'typescript'
                    elif file_path.endswith('.jsx') or file_path.endswith('.js'):
                        language = 'javascript'
                    elif file_path.endswith('.css'):
                        language = 'css'
                    elif file_path.endswith('.json'):
                        language = 'json'
                
                fs_write = emitter.emit_fs_write(
                    path=file_path,
                    kind="file",
                    language=language,
                    content=content if isinstance(content, str) else json.dumps(content)
                )
                yield yield_event(fs_write)
                await asyncio.sleep(0)
            
            complete_msg = emitter.emit_chat_message(f"Project modified successfully! {len(files)} files updated.")
            yield yield_event(complete_msg)
            await asyncio.sleep(0)
            
            complete_event = emitter.emit_stream_complete()
            yield yield_event(complete_event)
            await asyncio.sleep(0)
            return
        
        elif action == "chat":
            if not request.user_input:
                yield yield_error("validation", "user_input is required for chat")
                await asyncio.sleep(0)
                return
            
            user_input = request.user_input.strip()
            smaller_model = get_smaller_model(model_family=model_family)
            help_msg = emitter.emit_chat_message("Let me help you with that...")
            yield yield_event(help_msg)
            await asyncio.sleep(0)
            
            thinking_start = emitter.emit_thinking_start()
            yield yield_event(thinking_start)
            await asyncio.sleep(0)
            
            # Stream chat response - use edit.start for streaming chunks
            from events import EditStartEvent, EditEndEvent
            response_text = ""
            loop = asyncio.get_event_loop()
            stream_gen = generate_stream(user_input, model=smaller_model, model_family=model_family)
            
            edit_start_time = time.time()
            while True:
                chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
                if chunk is None:
                    break
                response_text += chunk
                # Use edit.start for streaming chat chunks
                edit_chunk = EditStartEvent.create(
                    path="chat_response",
                    content=chunk,
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                yield yield_event(edit_chunk)
                await asyncio.sleep(0)
            
            # Emit edit.end after streaming completes (per contract)
            edit_duration_ms = int((time.time() - edit_start_time) * 1000)
            edit_end = EditEndEvent.create(
                path="chat_response",
                duration_ms=edit_duration_ms,
                project_id=project_id,
                conversation_id=conversation_id
            )
            yield yield_event(edit_end)
            await asyncio.sleep(0)
            
            thinking_end = emitter.emit_thinking_end(duration_ms=1000)
            yield yield_event(thinking_end)
            await asyncio.sleep(0)
            
            final_msg = emitter.emit_chat_message(response_text)
            yield yield_event(final_msg)
            await asyncio.sleep(0)
            
            complete_event = emitter.emit_stream_complete()
            yield yield_event(complete_event)
            await asyncio.sleep(0)
            return
        
        else:
            yield yield_error("validation", f"Could not determine action from payload")
            await asyncio.sleep(0)
    
    except Exception as e:
        error_msg = str(e)
        error_event = emitter.emit_error(scope="runtime", message=error_msg)
        yield yield_event(error_event)
        await asyncio.sleep(0)
        stream_failed = emitter.emit_stream_failed()
        yield yield_event(stream_failed)
        await asyncio.sleep(0)


@app.post("/api/v1/stream")
async def stream_endpoint(request: StreamRequest):
    """Unified streaming endpoint for all LLM interactions"""
    return StreamingResponse(
        stream_events(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/v1/stream/message/")
async def stream_message_endpoint(request: MessageRequest):
    """
    Process user answers to LLM questions and continue/resume SSE streaming.
    
    All responses are converted into a user prompt that continues the conversation.
    """
    log("=" * 80)
    log("📨 POST /api/v1/stream/message/ - REQUEST RECEIVED")
    log("=" * 80)
    log(f"Project ID: {request.project_id}")
    log(f"Chat ID: {request.chat_id}")
    log(f"User Input: {request.user_input}")
    log(f"Number of responses: {len(request.responses)}")
    log("-" * 80)
    
    try:
        # Validate required fields
        log("🔍 Step 1: Validating required fields...")
        if not request.project_id:
            log("❌ Validation failed: project_id is required")
            raise HTTPException(status_code=400, detail="project_id is required")
        log("✓ project_id validated")
        
        if not request.chat_id:
            log("❌ Validation failed: chat_id is required")
            raise HTTPException(status_code=400, detail="chat_id is required")
        log("✓ chat_id validated")
        
        if not request.responses or len(request.responses) == 0:
            log("❌ Validation failed: responses array is required and cannot be empty")
            raise HTTPException(status_code=400, detail="responses array is required and cannot be empty")
        log(f"✓ responses array validated ({len(request.responses)} responses)")
        
        # Validate each response
        log("\n🔍 Step 2: Validating each response...")
        for idx, response in enumerate(request.responses):
            log(f"\n  Response[{idx}]:")
            log(f"    q_id: {response.q_id}")
            log(f"    q_type: {response.q_type}")
            log(f"    skipped: {response.skipped}")
            log(f"    content.label: {response.content.label}")
            
            if not response.q_id:
                log(f"    ❌ Missing q_id in response[{idx}]")
                raise HTTPException(status_code=400, detail=f"Missing q_id in response[{idx}]")
            
            if response.q_type not in ["open_ended", "mcq", "multi_select", "form"]:
                log(f"    ❌ Invalid q_type '{response.q_type}' in response[{idx}]")
                raise HTTPException(status_code=400, detail=f"Invalid q_type '{response.q_type}' in response[{idx}]. Must be one of: open_ended, mcq, multi_select, form")
            
            # Validate type-specific content fields
            content = response.content
            if response.q_type == "open_ended":
                log(f"    content.answer: {content.answer}")
                if content.selectedOption is not None or content.selectedOptions is not None or content.answers is not None:
                    log(f"    ❌ open_ended should only have 'answer' field")
                    raise HTTPException(status_code=400, detail=f"Response[{idx}]: open_ended should only have 'answer' field")
                log(f"    ✓ open_ended validation passed")
            elif response.q_type == "mcq":
                log(f"    content.selectedOption: {content.selectedOption}")
                if content.answer is not None or content.selectedOptions is not None or content.answers is not None:
                    log(f"    ❌ mcq should only have 'selectedOption' field")
                    raise HTTPException(status_code=400, detail=f"Response[{idx}]: mcq should only have 'selectedOption' field")
                log(f"    ✓ mcq validation passed")
            elif response.q_type == "multi_select":
                log(f"    content.selectedOptions: {content.selectedOptions}")
                if content.answer is not None or content.selectedOption is not None or content.answers is not None:
                    log(f"    ❌ multi_select should only have 'selectedOptions' field")
                    raise HTTPException(status_code=400, detail=f"Response[{idx}]: multi_select should only have 'selectedOptions' field")
                log(f"    ✓ multi_select validation passed")
            elif response.q_type == "form":
                log(f"    content.answers: {content.answers}")
                if content.answer is not None or content.selectedOption is not None or content.selectedOptions is not None:
                    log(f"    ❌ form should only have 'answers' field")
                    raise HTTPException(status_code=400, detail=f"Response[{idx}]: form should only have 'answers' field")
                log(f"    ✓ form validation passed")
        
        log("\n✓ All responses validated successfully")
        
        # Load conversation context using chat_id
        log(f"\n🔍 Step 3: Loading conversation context...")
        log(f"  Using chat_id as session_id: {request.chat_id}")
        session = get_or_create_session(request.chat_id)
        log(f"  ✓ Session loaded/created")
        log(f"  Session keys: {list(session.keys())}")
        
        # Process responses and build questionnaire_answers dict and user prompt
        log(f"\n🔍 Step 4: Processing responses and building user prompt...")
        questionnaire_answers = {}
        user_prompt_parts = []
        
        # Check for open_ended question (there should be only one, and it's always alone)
        open_ended_response = None
        for response in request.responses:
            if response.q_type == "open_ended":
                if open_ended_response is not None:
                    log("❌ Multiple open_ended questions found")
                    raise HTTPException(status_code=400, detail="Multiple open_ended questions found. Only one open_ended question is allowed.")
                open_ended_response = response
                log(f"  Found open_ended question: q_id={response.q_id}")
        
        # Validate open_ended behavior: should be alone
        if open_ended_response and len(request.responses) > 1:
            log("❌ open_ended question cannot be mixed with other question types")
            raise HTTPException(status_code=400, detail="open_ended question cannot be mixed with other question types")
        
        # Process all responses
        log(f"\n  Processing {len(request.responses)} response(s)...")
        for idx, response in enumerate(request.responses):
            if response.skipped:
                log(f"  Response[{idx}] (q_id: {response.q_id}) - SKIPPED, skipping processing")
                continue
            
            q_id = response.q_id
            q_type = response.q_type
            content = response.content
            label = content.label  # Question label from chat.question event
            
            log(f"\n  Response[{idx}] (q_id: {q_id}, type: {q_type}):")
            log(f"    Question: {label}")
            
            if q_type == "open_ended":
                if content.answer:
                    log(f"    Answer: {content.answer}")
                    user_prompt_parts.append(f"{label}: {content.answer}")
                    questionnaire_answers[q_id] = content.answer
                    log(f"    ✓ Stored in questionnaire_answers[{q_id}]")
                    
            elif q_type == "mcq":
                if content.selectedOption:
                    log(f"    Selected Option: {content.selectedOption}")
                    user_prompt_parts.append(f"{label}: {content.selectedOption}")
                    questionnaire_answers[q_id] = content.selectedOption
                    log(f"    ✓ Stored in questionnaire_answers[{q_id}]")
                else:
                    log(f"    ⚠️ No option selected (empty or None)")
                    
            elif q_type == "multi_select":
                if content.selectedOptions:
                    log(f"    Selected Options (IDs): {content.selectedOptions}")
                    # Try to map IDs to labels if available
                    question_options = session.get(f"question_options_{q_id}", [])
                    if question_options:
                        log(f"    Found stored question options: {len(question_options)} options")
                        options_dict = {opt.get("id"): opt.get("label") for opt in question_options}
                        selected_labels = [options_dict.get(opt_id, opt_id) for opt_id in content.selectedOptions]
                        selected_text = ", ".join(selected_labels)
                        log(f"    Mapped to labels: {selected_labels}")
                    else:
                        selected_text = ", ".join(content.selectedOptions)
                        log(f"    Using IDs directly (no stored options found)")
                    
                    user_prompt_parts.append(f"{label}: {selected_text}")
                    questionnaire_answers[q_id] = content.selectedOptions
                    log(f"    ✓ Stored in questionnaire_answers[{q_id}]")
                else:
                    log(f"    ⚠️ No options selected (empty list)")
                    
            elif q_type == "form":
                if content.answers:
                    log(f"    Form answers: {content.answers}")
                    form_parts = []
                    for field in content.answers:
                        field_label = field.get("label", "")
                        field_answer = field.get("answer", "")
                        if isinstance(field_answer, list):
                            field_answer = ", ".join(field_answer)
                        form_parts.append(f"{field_label}: {field_answer}")
                        log(f"      - {field_label}: {field_answer}")
                    form_text = ", ".join(form_parts)
                    user_prompt_parts.append(f"{label}: {form_text}")
                    
                    form_answers = {}
                    for field in content.answers:
                        field_label = field.get("label", "")
                        field_answer = field.get("answer", "")
                        form_answers[field_label] = field_answer
                    questionnaire_answers[q_id] = form_answers
                    log(f"    ✓ Stored in questionnaire_answers[{q_id}]")
        
        # Combine all responses into a user prompt
        combined_prompt = "\n".join(user_prompt_parts)
        log(f"\n  📝 Combined user prompt from responses:")
        if combined_prompt:
            log(f"  {combined_prompt}")
        else:
            log(f"  (empty - no responses processed)")
        
        # Add user_input if provided (additional text entered along with questions)
        if request.user_input:
            log(f"\n  📝 Adding user_input to prompt:")
            log(f"  {request.user_input}")
            if combined_prompt:
                combined_prompt = f"{combined_prompt}\n\nAdditional requirements: {request.user_input}"
            else:
                combined_prompt = request.user_input
            log(f"  ✓ Final combined prompt:")
            log(f"  {combined_prompt}")
        else:
            log(f"\n  ℹ️ No user_input provided")
        
        # Store questionnaire answers in session
        log(f"\n🔍 Step 5: Storing data in session...")
        session["questionnaire_answers"] = questionnaire_answers
        log(f"  ✓ Stored questionnaire_answers: {json.dumps(questionnaire_answers, indent=2)}")
        
        # Store the combined prompt as user_input for LLM continuation
        if combined_prompt:
            session["user_input_from_message"] = combined_prompt
            prompt_preview = combined_prompt[:100] + "..." if len(combined_prompt) > 100 else combined_prompt
            log(f"  ✓ Stored user_input_from_message: {prompt_preview}")
        
        # Store project_id and chat_id in session for context
        session["project_id"] = request.project_id
        session["chat_id"] = request.chat_id
        log(f"  ✓ Stored project_id: {request.project_id}")
        log(f"  ✓ Stored chat_id: {request.chat_id}")
        
        # Log final session state
        log(f"\n📊 Final Session State:")
        log(f"  Keys: {list(session.keys())}")
        log(f"  questionnaire_answers keys: {list(questionnaire_answers.keys())}")
        if "user_input_from_message" in session:
            log(f"  user_input_from_message length: {len(session['user_input_from_message'])} chars")
        
        # Step 7: Build system prompt and call LLM
        log(f"\n🔍 Step 7: Building system prompt and calling LLM...")
        
        # Get model family from session or default to gemini
        model_family = session.get("model_family", "gemini")
        log(f"  Model family: {model_family}")
        
        # Get page_type_key from session (should be set from previous stream request)
        page_type_key = session.get("page_type_key")
        log(f"  Page type key: {page_type_key}")
        
        # Build system prompt (same structure as generate_project)
        base_prompt = (
            "Return JSON only: React+Vite+TypeScript project. Schema: {\"project\": {\"name\": string, \"description\": string, \"files\": {...}, \"dirents\": {...}, \"meta\": {...}}}. Files: strings or {\"content\": \"...\"}.\n\n"
            "🚨 REACT APP ONLY - NO STATIC HTML 🚨\n\n"
            "REQUIRED:\n"
            "1. React 18+ + TypeScript (.tsx only, NO .html pages)\n"
            "2. Vite + @vitejs/plugin-react\n"
            "3. Structure: src/main.tsx, src/App.tsx (React Router), src/pages/*.tsx, src/components/*.tsx, src/types/*.ts\n"
            "4. package.json: React, React-DOM, Vite, TypeScript, react-router-dom\n"
            "5. React Router: BrowserRouter, Routes, Route\n"
            "6. Functional components + TypeScript interfaces\n"
            "7. React hooks: useState, useEffect, useContext\n"
            "8. Interactive: buttons/forms/nav work\n"
            "9. Styling: CSS Modules/styled-components/Tailwind (NOT inline HTML styles)\n"
            "10. index.html = entry only, all content via React\n\n"
            "FORBIDDEN: Static HTML pages, plain HTML/CSS, image-only layouts, missing Router/TypeScript.\n"
        )
        
        # Add page type specific instructions if available
        if page_type_key:
            page_type_config = get_page_type_by_key(page_type_key)
            if page_type_config:
                base_prompt += f"\n=== PAGE TYPE: {page_type_config['name']} ({page_type_config['category']}) ===\n"
                base_prompt += f"Target User: {page_type_config['end_user']}\n\n"
                base_prompt += "REQUIRED CORE PAGES:\n"
                for i, page in enumerate(page_type_config['core_pages'], 1):
                    base_prompt += f"{i}. {page}\n"
                base_prompt += "\n\nREQUIRED COMPONENTS TO IMPLEMENT:\n"
                for i, component in enumerate(page_type_config['components'], 1):
                    base_prompt += f"{i}. **{component['name']}**: {component['description']}\n"
                log(f"  ✓ Added page type context: {page_type_config['name']}")
        
        # Add questionnaire answers to system prompt
        if questionnaire_answers:
            base_prompt += "\n=== USER REQUIREMENTS (from questionnaire) ===\n"
            for key, value in questionnaire_answers.items():
                if isinstance(value, list):
                    base_prompt += f"- {key}\n  Selected: {', '.join(value)}\n"
                else:
                    base_prompt += f"- {key}\n  Answer: {value}\n"
            log(f"  ✓ Added questionnaire answers to system prompt")
        
        # Add wizard inputs if available
        wizard_inputs = session.get("wizard_inputs")
        if wizard_inputs:
            if isinstance(wizard_inputs, dict):
                wizard_data = wizard_inputs
            elif hasattr(wizard_inputs, 'dict'):
                wizard_data = wizard_inputs.dict()
            else:
                wizard_data = {}
            base_prompt += "\nUSER_FIELDS:\n" + json.dumps(wizard_data, ensure_ascii=False)
            log(f"  ✓ Added wizard inputs to system prompt")
        
        # Combine system prompt + user prompt
        final_prompt = base_prompt + "\n\n=== USER REQUEST ===\n" + combined_prompt
        
        log(f"  System prompt length: {len(base_prompt)} chars")
        log(f"  User prompt length: {len(combined_prompt)} chars")
        log(f"  Final prompt length: {len(final_prompt)} chars")
        
        # Get model for generation
        from models.model_factory import get_provider
        try:
            provider = get_provider(model_family)
            webpage_model = provider.get_default_model()
            log(f"  Using model: {webpage_model}")
        except Exception as e:
            log(f"  ❌ Failed to get provider: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize {model_family} provider: {str(e)}")
        
        log(f"\n✅ Step 8: Starting LLM stream...")
        log("=" * 80)
        
        # Return streaming response
        return StreamingResponse(
            stream_project_generation_from_message(
                final_prompt=final_prompt,
                model=webpage_model,
                model_family=model_family,
                project_id=request.project_id,
                conversation_id=request.chat_id,
                session=session
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except HTTPException as e:
        log(f"\n❌ HTTPException: {e.status_code} - {e.detail}")
        log("=" * 80)
        raise
    except Exception as e:
        log(f"\n❌ Exception: {str(e)}")
        log(f"  Type: {type(e).__name__}")
        import traceback
        log(f"  Traceback:\n{traceback.format_exc()}")
        log("=" * 80)
        log(f"[MESSAGE_ENDPOINT_ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def stream_project_generation_from_message(
    final_prompt: str,
    model: str,
    model_family: str,
    project_id: str,
    conversation_id: str,
    session: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Stream project generation after message processing - combines system prompt + user prompt"""
    # Initialize event system
    event_logger = get_event_logger()
    emitter = EventEmitter(
        project_id=project_id,
        conversation_id=conversation_id,
        callback=lambda event: event_logger.log_event(event)
    )
    
    def yield_event(event: EventEnvelope):
        """Yield an event in proper SSE format"""
        return f"data: {event.to_json()}\n\n"
    
    try:
        log(f"[STREAM_GENERATION] Starting project generation stream")
        log(f"[STREAM_GENERATION] Model: {model} ({model_family})")
        log(f"[STREAM_GENERATION] Prompt length: {len(final_prompt)} chars")
        
        # Emit progress events
        progress_init = emitter.emit_progress_init(
            steps=[
                {"id": "prepare", "label": "Preparing", "status": "in_progress"},
                {"id": "generate", "label": "Generating", "status": "pending"},
                {"id": "parse", "label": "Parsing", "status": "pending"},
                {"id": "save", "label": "Saving", "status": "pending"},
            ],
            mode="inline"
        )
        yield yield_event(progress_init)
        await asyncio.sleep(0)
        
        progress_prepare = emitter.emit_progress_update("prepare", "completed")
        yield yield_event(progress_prepare)
        await asyncio.sleep(0)
        
        progress_generate = emitter.emit_progress_update("generate", "in_progress")
        yield yield_event(progress_generate)
        await asyncio.sleep(0)
        
        thinking_start = emitter.emit_thinking_start()
        yield yield_event(thinking_start)
        await asyncio.sleep(0)
        
        gen_msg = emitter.emit_chat_message(f"Generating project using {model} ({model_family})...")
        yield yield_event(gen_msg)
        await asyncio.sleep(0)
        
        start_time = time.time()
        
        # Stream the generation
        from events import EditStartEvent, EditEndEvent
        output = ""
        loop = asyncio.get_event_loop()
        stream_gen = generate_stream(final_prompt, model=model, model_family=model_family)
        
        log(f"[STREAM_GENERATION] Starting LLM stream...")
        edit_start_time = time.time()
        chunk_count = 0
        while True:
            chunk = await loop.run_in_executor(None, _next_chunk, stream_gen)
            if chunk is None:
                break
            output += chunk
            chunk_count += 1
            edit_chunk = EditStartEvent.create(
                path="project_generation",
                content=chunk,
                project_id=project_id,
                conversation_id=conversation_id
            )
            yield yield_event(edit_chunk)
            # Small delay to ensure real-time streaming (Postman may buffer, but this helps)
            await asyncio.sleep(0.01)
        
        # Emit edit.end after streaming completes (per contract)
        edit_duration_ms = int((time.time() - edit_start_time) * 1000)
        edit_end = EditEndEvent.create(
            path="project_generation",
            duration_ms=edit_duration_ms,
            project_id=project_id,
            conversation_id=conversation_id
        )
        yield yield_event(edit_end)
        await asyncio.sleep(0.01)
        log(f"[STREAM_GENERATION] ✓ edit.end emitted: path=project_generation, duration={edit_duration_ms}ms")
        
        log(f"[STREAM_GENERATION] Received {chunk_count} chunks, total length: {len(output)} chars")
        
        elapsed_time = time.time() - start_time
        thinking_end = emitter.emit_thinking_end(duration_ms=int(elapsed_time * 1000))
        yield yield_event(thinking_end)
        await asyncio.sleep(0)
        
        progress_gen_complete = emitter.emit_progress_update("generate", "completed")
        yield yield_event(progress_gen_complete)
        await asyncio.sleep(0)
        
        progress_parse = emitter.emit_progress_update("parse", "in_progress")
        yield yield_event(progress_parse)
        await asyncio.sleep(0)
        
        if not output or len(output) < 100:
            log(f"[STREAM_GENERATION] ❌ Empty or very short output: {len(output)} chars")
            parse_failed = emitter.emit_progress_update("parse", "failed")
            yield yield_event(parse_failed)
            await asyncio.sleep(0)
            
            error_event = emitter.emit_error(
                scope="validation",
                message="Failed to parse JSON from model output",
                details="The model may have returned invalid JSON or non-JSON content.",
                actions=["retry", "ask_user"]
            )
            yield yield_event(error_event)
            await asyncio.sleep(0)
            
            stream_failed = emitter.emit_stream_failed()
            yield yield_event(stream_failed)
            await asyncio.sleep(0)
            return
        
        log(f"[STREAM_GENERATION] Parsing JSON output...")
        project = parse_project_json(output)
        
        if not project:
            log(f"[STREAM_GENERATION] ❌ Failed to parse JSON")
            parse_failed = emitter.emit_progress_update("parse", "failed")
            yield yield_event(parse_failed)
            await asyncio.sleep(0)
            
            error_event = emitter.emit_error(
                scope="validation",
                message="Failed to parse JSON from model output",
                details="The model may have returned invalid JSON or non-JSON content.",
                actions=["retry", "ask_user"]
            )
            yield yield_event(error_event)
            await asyncio.sleep(0)
            
            stream_failed = emitter.emit_stream_failed()
            yield yield_event(stream_failed)
            await asyncio.sleep(0)
            return
        
        log(f"[STREAM_GENERATION] ✓ JSON parsed successfully, {len(project.get('files', {}))} files")
        
        parse_complete = emitter.emit_progress_update("parse", "completed")
        yield yield_event(parse_complete)
        await asyncio.sleep(0)
        
        save_progress = emitter.emit_progress_update("save", "in_progress")
        yield yield_event(save_progress)
        await asyncio.sleep(0)
        
        parsed_msg = emitter.emit_chat_message(f"JSON parsed successfully. Project has {len(project.get('files', {}))} files.")
        yield yield_event(parsed_msg)
        await asyncio.sleep(0)
        
        # Save project
        project_json_path = f"{OUTPUT_DIR}/project.json"
        with open(project_json_path, "w") as f:
            json.dump({"project": project}, f, indent=2)
        
        log(f"[STREAM_GENERATION] ✓ Saved project.json")
        
        # Emit fs.write for project.json - MUST be streamed per contract (fs.write is single source of truth)
        fs_write_project = emitter.emit_fs_write(
            path="project.json",
            kind="file",
            language="json",
            content=json.dumps({"project": project}, indent=2)
        )
        yield yield_event(fs_write_project)
        await asyncio.sleep(0)
        
        # Save all files
        files = project.get('files', {})
        log(f"[STREAM_GENERATION] Saving {len(files)} files...")
        for file_path, file_content in files.items():
            if isinstance(file_content, dict):
                content = file_content.get('content', '')
                language = file_content.get('language', None)
            else:
                content = file_content
                language = None
            
            if not language:
                if file_path.endswith('.tsx') or file_path.endswith('.ts'):
                    language = 'typescript'
                elif file_path.endswith('.jsx') or file_path.endswith('.js'):
                    language = 'javascript'
                elif file_path.endswith('.css'):
                    language = 'css'
                elif file_path.endswith('.json'):
                    language = 'json'
                elif file_path.endswith('.html'):
                    language = 'html'
            
            # Emit fs.write for each file - MUST be streamed per contract
            fs_write = emitter.emit_fs_write(
                path=file_path,
                kind="file",
                language=language,
                content=content if isinstance(content, str) else json.dumps(content)
            )
            yield yield_event(fs_write)
            await asyncio.sleep(0)
        
        save_project_files(project, f"{OUTPUT_DIR}/project")
        log(f"[STREAM_GENERATION] ✓ All files saved")
        
        save_complete = emitter.emit_progress_update("save", "completed")
        yield yield_event(save_complete)
        await asyncio.sleep(0)
        
        success_msg = emitter.emit_chat_message("Base project generated successfully!")
        yield yield_event(success_msg)
        await asyncio.sleep(0)
        
        complete_event = emitter.emit_stream_complete()
        yield yield_event(complete_event)
        await asyncio.sleep(0)
        
        log(f"[STREAM_GENERATION] ✅ Stream complete")
        
    except Exception as e:
        error_msg = str(e)
        log(f"[STREAM_GENERATION_ERROR] {error_msg}")
        import traceback
        log(f"[STREAM_GENERATION_ERROR] Traceback:\n{traceback.format_exc()}")
        error_event = emitter.emit_error(scope="runtime", message=error_msg)
        yield yield_event(error_event)
        await asyncio.sleep(0)
        stream_failed = emitter.emit_stream_failed()
        yield yield_event(stream_failed)
        await asyncio.sleep(0)


@app.post("/api/v1/classify-intent", response_model=IntentResponse)
async def classify_intent_endpoint(request: IntentRequest):
    """Classify user intent and return appropriate response"""
    user_input = request.user_input.strip()
    
    if not user_input:
        raise HTTPException(status_code=400, detail="User input cannot be empty")
    
    # Classify intent (default to gemini for backward compatibility)
    model_family = getattr(request, 'model_family', 'gemini') if hasattr(request, 'model_family') else 'gemini'
    label, meta = classify_intent(user_input, model_family=model_family)
    log(f"[CLASSIFY] label={label} meta={meta} model_family={model_family}")
    
    response = IntentResponse(
        label=label,
        meta=meta
    )
    
    if label == "greeting_only":
        response.greeting_response = generate_greeting_response(user_input)
        return response
    
    if label == "illegal":
        raise HTTPException(status_code=403, detail="Sorry — I can't help with that request.")
    
    if label == "chat":
        smaller_model = get_smaller_model(model_family=model_family)
        response.chat_response = chat_response(user_input, model_family=model_family)
        response.meta["model"] = smaller_model
        response.meta["model_family"] = model_family
        return response
    
    if label == "webpage_build":
        # Classify page type
        page_type_key, page_type_meta = classify_page_type(user_input, model_family=model_family)
        log(f"[PAGE_TYPE] key={page_type_key} meta={page_type_meta}")
        response.page_type_key = page_type_key
        response.page_type_meta = page_type_meta
        
        # Analyze if query needs follow-up questions
        needs_followup, detail_confidence = analyze_query_detail(user_input, model_family=model_family)
        log(f"[DETAIL_ANALYSIS] needs_followup={needs_followup} confidence={detail_confidence}")
        
        if page_type_key == "generic":
            response.needs_page_type_selection = True
        elif needs_followup and has_questionnaire(page_type_key):
            response.needs_questionnaire = True
        else:
            response.needs_questionnaire = False
        
        return response
    
    raise HTTPException(status_code=400, detail="I didn't fully understand — please clarify.")


@app.get("/api/v1/page-types")
async def get_page_types():
    """Get all available page types/categories"""
    categories = get_all_categories()
    return {"categories": categories}


@app.get("/api/v1/questionnaire/{page_type_key}")
async def get_questionnaire_endpoint(page_type_key: str):
    """Get questionnaire for a specific page type"""
    if not has_questionnaire(page_type_key):
        return {"has_questionnaire": False, "questionnaire": None}
    
    questionnaire = get_questionnaire(page_type_key)
    return {
        "has_questionnaire": True,
        "questionnaire": questionnaire
    }


@app.post("/api/v1/generate-project", response_model=ProjectResponse)
async def generate_project_endpoint(request: GenerateProjectRequest, background_tasks: BackgroundTasks):
    """Generate a project based on user inputs"""
    session = get_or_create_session(request.session_id)
    
    # Initialize event system
    event_logger = get_event_logger()
    project_id = f"proj_{int(time.time())}"
    conversation_id = f"conv_{int(time.time())}"
    emitter = EventEmitter(
        project_id=project_id,
        conversation_id=conversation_id,
        callback=lambda event: event_logger.log_event(event)
    )
    
    # Emit initial events
    emitter.emit_chat_message("Starting project generation...")
    
    # Build the prompt
    base_prompt = (
        "Return JSON only: React+Vite+TypeScript project. Schema: {\"project\": {\"name\": string, \"description\": string, \"files\": {...}, \"dirents\": {...}, \"meta\": {...}}}. Files: strings or {\"content\": \"...\"}.\n\n"
        
        "🚨 REACT APP ONLY - NO STATIC HTML 🚨\n\n"
        
        "REQUIRED:\n"
        "1. React 18+ + TypeScript (.tsx only, NO .html pages)\n"
        "2. Vite + @vitejs/plugin-react\n"
        "3. Structure: src/main.tsx, src/App.tsx (React Router), src/pages/*.tsx, src/components/*.tsx, src/types/*.ts\n"
        "4. package.json: React, React-DOM, Vite, TypeScript, react-router-dom\n"
        "5. React Router: BrowserRouter, Routes, Route\n"
        "6. Functional components + TypeScript interfaces\n"
        "7. React hooks: useState, useEffect, useContext\n"
        "8. Interactive: buttons/forms/nav work\n"
        "9. Styling: CSS Modules/styled-components/Tailwind (NOT inline HTML styles)\n"
        "10. index.html = entry only, all content via React\n\n"
        
        "FORBIDDEN: Static HTML pages, plain HTML/CSS, image-only layouts, missing Router/TypeScript.\n"
    )
    
    # Add page type specific requirements
    page_type_key = request.page_type_key or session.get("page_type_key")
    if page_type_key:
        page_type_config = get_page_type_by_key(page_type_key)
        if page_type_config:
            emitter.emit_chat_message(f"Configuring {page_type_config['name']} requirements...")
            
            base_prompt += f"\n=== PAGE TYPE: {page_type_config['name']} ({page_type_config['category']}) ===\n"
            base_prompt += f"Target User: {page_type_config['end_user']}\n\n"
            
            base_prompt += "REQUIRED CORE PAGES:\n"
            for i, page in enumerate(page_type_config['core_pages'], 1):
                base_prompt += f"{i}. {page}\n"
            
            base_prompt += "\n\nREQUIRED COMPONENTS TO IMPLEMENT:\n"
            for i, component in enumerate(page_type_config['components'], 1):
                base_prompt += f"{i}. **{component['name']}**: {component['description']}\n"
            
            if "Auth Module" in page_type_config.get('core_pages', []):
                base_prompt += "\n\nAUTHENTICATION NOTE:\n"
                base_prompt += "- For 'Auth Module', create a SIMPLE login page (no backend required)\n"
                base_prompt += "- Use mock authentication (hardcoded credentials or localStorage)\n"
                base_prompt += "- Focus on the UI/UX, not complex auth flows\n"
                base_prompt += "- The main app should be accessible after simple login\n"
                base_prompt += "- Skip complex features like password reset, email verification, OAuth for now\n\n"
            
            base_prompt += "\n\nIMPORTANT: Implement ALL core pages and components. Each must be fully functional React components with TypeScript. Include proper routing.\n\n"
    
    # Add questionnaire answers if available
    questionnaire_answers = request.questionnaire_answers or session.get("questionnaire_answers", {})
    if questionnaire_answers:
        base_prompt += "\n=== USER REQUIREMENTS (from questionnaire) ===\n"
        for key, value in questionnaire_answers.items():
            if isinstance(value, list):
                formatted_value = ', '.join(value)
                base_prompt += f"- {key}\n  Selected: {formatted_value}\n"
            else:
                base_prompt += f"- {key}\n  Answer: {value}\n"
        base_prompt += "\nIMPORTANT: Use these specific requirements to tailor the design, content, features, and functionality.\n\n"
    
    # Add wizard inputs
    wizard_data = request.wizard_inputs.dict()
    final_prompt = base_prompt + "USER_FIELDS:\n" + json.dumps(wizard_data, ensure_ascii=False)
    
    # Get default model for the specified family
    from models.model_factory import get_provider
    try:
        provider = get_provider(model_family)
        webpage_model = provider.get_default_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize {model_family} provider: {str(e)}")
    
    emitter.emit_progress_init(
        steps=[
            {"id": "prepare", "label": "Preparing", "status": "in_progress"},
            {"id": "generate", "label": "Generating", "status": "pending"},
            {"id": "parse", "label": "Parsing", "status": "pending"},
            {"id": "save", "label": "Saving", "status": "pending"},
        ],
        mode="inline"
    )
    
    emitter.emit_progress_update("prepare", "completed")
    emitter.emit_progress_update("generate", "in_progress")
    emitter.emit_thinking_start()
    
    start_time = time.time()
    
    try:
        emitter.emit_chat_message(f"Generating project using {webpage_model} ({model_family})...")
        output = generate_text(final_prompt, model=webpage_model, model_family=model_family, fallback_models=None)
        elapsed_time = time.time() - start_time
        emitter.emit_thinking_end(duration_ms=int(elapsed_time * 1000))
        emitter.emit_progress_update("generate", "completed")
        emitter.emit_progress_update("parse", "in_progress")
        
        if not output or len(output) < 100:
            raise HTTPException(status_code=500, detail="Model returned empty or very short output")
        
        project = parse_project_json(output)
        
        if not project:
            emitter.emit_progress_update("parse", "failed")
            emitter.emit_error(
                scope="validation",
                message="Failed to parse JSON from model output",
                details="The model may have returned invalid JSON or non-JSON content.",
                actions=["retry", "ask_user"]
            )
            emitter.emit_stream_failed()
            raise HTTPException(status_code=500, detail="Failed to parse JSON from model output")
        
        emitter.emit_progress_update("parse", "completed")
        emitter.emit_progress_update("save", "in_progress")
        emitter.emit_chat_message(f"JSON parsed successfully. Project has {len(project.get('files', {}))} files.")
        
        # Save project
        project_json_path = f"{OUTPUT_DIR}/project.json"
        with open(project_json_path, "w") as f:
            json.dump({"project": project}, f, indent=2)
        
        emitter.emit_fs_write(
            path="project.json",
            kind="file",
            language="json",
            content=json.dumps({"project": project}, indent=2)
        )
        
        # Save all files
        files = project.get('files', {})
        for file_path, file_content in files.items():
            if isinstance(file_content, dict):
                content = file_content.get('content', '')
                language = file_content.get('language', None)
            else:
                content = file_content
                language = None
            
            if not language:
                if file_path.endswith('.tsx') or file_path.endswith('.ts'):
                    language = 'typescript'
                elif file_path.endswith('.jsx') or file_path.endswith('.js'):
                    language = 'javascript'
                elif file_path.endswith('.css'):
                    language = 'css'
                elif file_path.endswith('.json'):
                    language = 'json'
                elif file_path.endswith('.html'):
                    language = 'html'
            
            emitter.emit_fs_write(
                path=file_path,
                kind="file",
                language=language,
                content=content if isinstance(content, str) else json.dumps(content)
            )
        
        save_project_files(project, f"{OUTPUT_DIR}/project")
        
        emitter.emit_progress_update("save", "completed")
        emitter.emit_chat_message("Base project generated successfully!")
        emitter.emit_stream_complete()
        
        events_file = f"{OUTPUT_DIR}/events.jsonl"
        
        return ProjectResponse(
            success=True,
            project_path=f"{OUTPUT_DIR}/project",
            project_json_path=project_json_path,
            files_count=len(files),
            message="Base project generated successfully!",
            events_file=events_file if os.path.exists(events_file) else None
        )
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Rate limit" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait a few minutes and try again."
            )
        raise HTTPException(status_code=500, detail=f"Error during generation: {error_msg}")


@app.post("/api/v1/modify-project", response_model=ProjectResponse)
async def modify_project_endpoint(request: ModifyProjectRequest):
    """Modify an existing project"""
    session = get_or_create_session(request.session_id)
    
    # Get base project
    base_path = request.base_project_path or session.get("last_project_path")
    if not base_path:
        base_path, _ = get_latest_project()
    
    if not base_path or not os.path.exists(base_path):
        raise HTTPException(status_code=404, detail="Base project not found")
    
    with open(base_path) as f:
        base_project = json.load(f)["project"]
    
    # Get model_family from request
    model_family = getattr(request, 'model_family', 'gemini') if hasattr(request, 'model_family') else 'gemini'
    
    # Classify modification complexity
    complexity, complexity_meta = classify_modification_complexity(request.instruction, model_family=model_family)
    mod_model = get_model_for_complexity(complexity, model_family=model_family)
    
    mod_prompt = f"""Modify project JSON. Return JSON only: {{"project": {{...}}}}. Match base schema. Change ONLY requested parts, keep rest unchanged. NO markdown/code blocks/explanations. Raw JSON only.

Base: {json.dumps({"project": base_project}, indent=2)}
Request: {request.instruction}"""
    
    try:
        mod_out = generate_text(mod_prompt, model=mod_model, model_family=model_family)
        mod_project = parse_project_json(mod_out)
        
        if not mod_project:
            # Retry with default model for the family if smaller model failed
            from models.model_factory import get_provider
            provider = get_provider(model_family)
            default_model = provider.get_default_model()
            if mod_model != default_model:
                mod_out = generate_text(mod_prompt, model=default_model, model_family=model_family)
                mod_project = parse_project_json(mod_out)
            
            if not mod_project:
                raise HTTPException(status_code=500, detail="Invalid modification output - model did not return valid JSON")
        
        # Validate structure
        if not isinstance(mod_project, dict) or "files" not in mod_project:
            raise HTTPException(status_code=500, detail="Invalid project structure")
        
        # Save modified project
        version = f"project_{int(time.time())}"
        dest = os.path.join(MODIFIED_DIR, version)
        os.makedirs(dest, exist_ok=True)
        
        project_json_path = os.path.join(dest, "project.json")
        with open(project_json_path, "w") as f:
            json.dump({"project": mod_project}, f, indent=2)
        
        save_project_files(mod_project, os.path.join(dest, "project"))
        
        session["last_project_path"] = project_json_path
        session["history"]["modifications"].append({
            "instruction": request.instruction,
            "from": base_path,
            "to": dest,
        })
        
        return ProjectResponse(
            success=True,
            project_path=os.path.join(dest, "project"),
            project_json_path=project_json_path,
            files_count=len(mod_project.get('files', {})),
            message="Modification saved successfully!",
            events_file=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Rate limit" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait a few minutes and try again."
            )
        raise HTTPException(status_code=500, detail=f"Error during modification: {error_msg}")


@app.get("/api/v1/latest-project")
async def get_latest_project_endpoint():
    """Get the latest generated project"""
    base_path, base_project = get_latest_project()
    
    if not base_path:
        raise HTTPException(status_code=404, detail="No project found")
    
    return {
        "project_path": base_path,
        "project": base_project
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

