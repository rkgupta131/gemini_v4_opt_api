# app.py
import os
import json
import time
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import log
from utils.event_logger import get_event_logger
from intent.greeting_generator import generate_greeting_response
from events import EventEmitter

from models.gemini_client import (
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


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
# if "step" not in st.session_state:
#     st.session_state.step = 0

# if "wizard_mode" not in st.session_state:
#     st.session_state.wizard_mode = "manual"

# if "collected" not in st.session_state:
#     st.session_state.collected = {}

if "history" not in st.session_state:
    st.session_state.history = {
        "initial_query": "",
        "wizard_inputs": {},
        "modifications": [],
    }
# Session state init
if "step" not in st.session_state:
    st.session_state.step = 0
if "collected" not in st.session_state:
    st.session_state.collected = {}
if "initial_intent" not in st.session_state:
    st.session_state.initial_intent = ""
if "final_summary" not in st.session_state:
    st.session_state.final_summary = ""
if "last_project_path" not in st.session_state:
    st.session_state.last_project_path = ""
if "last_output_text" not in st.session_state:
    st.session_state.last_output_text = ""
if "page_type_key" not in st.session_state:
    st.session_state.page_type_key = ""
if "page_type_config" not in st.session_state:
    st.session_state.page_type_config = None
if "needs_questionnaire" not in st.session_state:
    st.session_state.needs_questionnaire = False
if "questionnaire_answers" not in st.session_state:
    st.session_state.questionnaire_answers = {}
if "selected_page_category" not in st.session_state:
    st.session_state.selected_page_category = None
if "questionnaire_emitter" not in st.session_state:
    st.session_state.questionnaire_emitter = None
if "must_have_features" not in st.session_state:
    st.session_state.must_have_features = {}
if "competitor_suggestions" not in st.session_state:
    st.session_state.competitor_suggestions = {}
# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("🧱 Webpage Builder AI")

# --------------------------------------------------
# STEP 0 — INTENT / CHAT
# --------------------------------------------------
# if st.session_state.step == 0:
#     user_input = st.text_area("What do you want to build or modify?")

#     if st.button("Continue"):
#         label, _ = classify_intent(user_input)
#         st.session_state.history["initial_query"] = user_input

#         if label == "chat":
#             st.write(chat_response(user_input))
#             st.stop()

#         if label == "webpage_build":
#             st.session_state.step = 1
#             st.rerun()

#         st.info("Please clarify your request.")
#         st.stop()
if st.session_state.step == 0:
    user_input = st.text_area("Tell me what you want to build or ask (chat):", height=140)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Chat / Classify"):
            if not user_input.strip():
                st.error("Please enter something.")
                st.stop()
            label, meta = classify_intent(user_input)
            st.session_state.history["initial_query"] = user_input
            log(f"[CLASSIFY] label={label} meta={meta}")
            # Display intent classification result
            st.info(f"🔍 **Intent Classification:** {label.upper()} | Model: {meta.get('model', 'N/A')} | Confidence: {meta.get('confidence', 0.0):.2f}")
            if label == "greeting_only":
                st.success(generate_greeting_response(user_input))
                st.stop()
            if label == "illegal":
                st.error("Sorry — I can't help with that request.")
                st.stop()
            if label == "chat":
                response = chat_response(user_input)
                smaller_model = get_smaller_model()
                st.info(f"💬 **Chat Response** (Model: {smaller_model})\n\n{response}")
                st.stop()
            if label == "webpage_build":
                st.session_state.initial_intent = user_input
                
                # Classify page type
                page_type_key, page_type_meta = classify_page_type(user_input)
                st.session_state.page_type_key = page_type_key
                log(f"[PAGE_TYPE] key={page_type_key} meta={page_type_meta}")
                # Display page type classification
                st.info(f"📄 **Page Type:** {page_type_key} | Model: {page_type_meta.get('model', 'N/A')} | Confidence: {page_type_meta.get('confidence', 0.0):.2f}")
                
                # Get page type configuration
                page_type_config = get_page_type_by_key(page_type_key)
                st.session_state.page_type_config = page_type_config
                
                # Analyze if query needs follow-up questions
                needs_followup, detail_confidence = analyze_query_detail(user_input)
                log(f"[DETAIL_ANALYSIS] needs_followup={needs_followup} confidence={detail_confidence}")
                # Display query detail analysis
                smaller_model = get_smaller_model()
                st.info(f"📊 **Query Detail Analysis:** needs_followup={needs_followup} | Model: {smaller_model} | Confidence: {detail_confidence:.2f}")
                
                if page_type_config:
                    st.success(f"✨ Detected page type: **{page_type_config['name']}** ({page_type_config['category']})")
                    st.info(f"This will include features like: {', '.join([c['name'] for c in page_type_config['components'][:3]])}...")
                else:
                    st.info("Building a generic webpage...")
                
                # Decide the next step based on query specificity
                if page_type_key == "generic":
                    # Very vague query - ask user to select page type first
                    st.info("🎯 Let's start by selecting what type of page you want to build!")
                    st.session_state.step = 0.3  # Go to page type selector
                elif needs_followup and has_questionnaire(page_type_key):
                    # Somewhat vague - show category-specific questionnaire
                    st.session_state.needs_questionnaire = True
                    st.info("💬 Let's gather some more details to make this perfect for you!")
                    st.session_state.step = 0.5  # Go to questionnaire step
                else:
                    # Detailed enough - skip to wizard mode
                    st.session_state.needs_questionnaire = False
                    st.session_state.step = 1  # Skip to wizard mode
                
                st.rerun()
            st.info("I didn't fully understand — please clarify.")
            st.stop()

    with col2:
        if st.button("Start Builder (skip classification)"):
            st.session_state.initial_intent = user_input
            # Still classify page type even if skipping intent classification
            if user_input.strip():
                page_type_key, page_type_meta = classify_page_type(user_input)
                st.session_state.page_type_key = page_type_key
                page_type_config = get_page_type_by_key(page_type_key)
                st.session_state.page_type_config = page_type_config
                
                # Check if needs category selection or questionnaire
                if page_type_key == "generic":
                    st.session_state.step = 0.3  # Page type selector
                else:
                    needs_followup, _ = analyze_query_detail(user_input)
                    if needs_followup and has_questionnaire(page_type_key):
                        st.session_state.needs_questionnaire = True
                        st.session_state.step = 0.5
                    else:
                        st.session_state.step = 1
            else:
                st.session_state.step = 1
            st.rerun()

    st.stop()

# --------------------------------------------------
# STEP 0.3 — PAGE TYPE SELECTOR (FOR GENERIC QUERIES)
# --------------------------------------------------
if st.session_state.step == 0.3:
    st.subheader("🎯 What type of page do you want to build?")
    st.markdown("Select the category that best matches your needs:")
    st.markdown("---")
    
    # Get all categories
    categories = get_all_categories()
    
    # Create options list for radio buttons
    category_options = []
    category_keys = []
    
    for key, info in categories.items():
        option_text = f"{info['icon']} {info['display_name']}"
        category_options.append(option_text)
        category_keys.append(key)
    
    # Show radio buttons for selection
    selected_option = st.radio(
        "Choose a page type:",
        category_options,
        index=0,
        label_visibility="collapsed"
    )
    
    # Get the selected category key
    selected_index = category_options.index(selected_option)
    selected_key = category_keys[selected_index]
    selected_info = categories[selected_key]
    
    # Show details for selected option
    with st.expander("📋 See details about this option", expanded=True):
        st.markdown(f"**Description:** {selected_info['description']}")
        st.markdown(f"**Examples:** {selected_info['examples']}")
    
    st.markdown("---")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    
    with col2:
        if st.button("Continue →", use_container_width=True, type="primary"):
            # User confirmed selection
            st.session_state.selected_page_category = selected_key
            st.session_state.page_type_key = selected_key
            
            # Update page type config
            page_type_config = get_page_type_by_key(selected_key)
            st.session_state.page_type_config = page_type_config
            
            # Show success message
            st.success(f"✨ Great! Building a {selected_info['display_name']}")
            
            # Go to questionnaire for this specific type
            if has_questionnaire(selected_key):
                st.session_state.needs_questionnaire = True
                st.session_state.step = 0.5
            else:
                st.session_state.step = 1
            
            st.rerun()

# --------------------------------------------------
# STEP 0.5 — MCQ QUESTIONNAIRE (CONDITIONAL)
# --------------------------------------------------
if st.session_state.step == 0.5:
    st.subheader("📋 Tell us more about your project")
    
    page_type_config = st.session_state.page_type_config
    if page_type_config:
        st.info(f"Building: **{page_type_config['name']}**")
    
    # Initialize event emitter for questionnaire if not already initialized
    if st.session_state.questionnaire_emitter is None:
        event_logger = get_event_logger()
        project_id = f"proj_{int(time.time())}"
        conversation_id = f"conv_{int(time.time())}"
        st.session_state.questionnaire_emitter = EventEmitter(
            project_id=project_id,
            conversation_id=conversation_id,
            callback=lambda event: event_logger.log_event(event)
        )
        # Store IDs for later use in generation step
        st.session_state.project_id = project_id
        st.session_state.conversation_id = conversation_id
    
    emitter = st.session_state.questionnaire_emitter
    
    # Get questionnaire for this page type
    questionnaire = get_questionnaire(st.session_state.page_type_key)
    
    if questionnaire:
        # Emit chat message indicating questionnaire start
        emitter.emit_chat_message("I need to gather some additional information to create the perfect page for you.")
        
        # Emit question events for each question in the questionnaire
        # Map questionnaire types to contract types
        type_mapping = {
            "radio": "mcq",
            "multiselect": "multi_select"
        }
        
        answers = st.session_state.questionnaire_answers
        
        # Track if this is the first render to emit events
        questions_emitted_key = f"questions_emitted_{st.session_state.page_type_key}"
        if questions_emitted_key not in st.session_state:
            st.session_state[questions_emitted_key] = False
        
        # Emit events for all questions if not already emitted
        if not st.session_state[questions_emitted_key]:
            for question_data in questionnaire["questions"]:
                q_id = question_data["id"]
                q_text = question_data["question"]
                q_type = question_data["type"]
                options = question_data["options"]
                
                # Map questionnaire type to contract type
                contract_type = type_mapping.get(q_type, "open_ended")
                
                # Build content based on question type
                content = {}
                if contract_type in ["mcq", "multi_select"]:
                    content["options"] = options
                
                # Emit question event (questions are not skippable by default)
                # According to LLM_Question_Streaming_Contract_FULL.docx
                emitter.emit_chat_question(
                    q_id=q_id,
                    question_type=contract_type,
                    label=q_text,
                    is_skippable=False,  # Questions are required
                    content=content
                )
            
            # Mark questions as emitted
            st.session_state[questions_emitted_key] = True
            
            # Emit stream.await_input to indicate we're waiting for user responses
            emitter.emit_stream_await_input(reason="suggestion")
        
        st.markdown("Please answer the following questions to help us create the perfect page for you:")
        st.markdown("---")
        
        # Render each question
        for question_data in questionnaire["questions"]:
            q_id = question_data["id"]
            q_text = question_data["question"]
            q_type = question_data["type"]
            options = question_data["options"]
            
            st.markdown(f"**{q_text}**")
            
            if q_type == "radio":
                # Radio buttons (single select)
                current_value = answers.get(q_id, options[0])
                selected = st.radio(
                    label=q_text,
                    options=options,
                    index=options.index(current_value) if current_value in options else 0,
                    key=f"q_{q_id}",
                    label_visibility="collapsed"
                )
                answers[q_id] = selected
                
            elif q_type == "multiselect":
                # Multiselect (multiple selections)
                current_value = answers.get(q_id, [])
                selected = st.multiselect(
                    label=q_text,
                    options=options,
                    default=current_value if isinstance(current_value, list) else [],
                    key=f"q_{q_id}",
                    label_visibility="collapsed"
                )
                answers[q_id] = selected
            
            st.markdown("---")
        
        # Update session state
        st.session_state.questionnaire_answers = answers
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("← Back"):
                st.session_state.step = 0
                st.rerun()
        
        with col2:
            if st.button("Continue →"):
                # Validate that all required questions are answered
                all_answered = True
                for question_data in questionnaire["questions"]:
                    q_id = question_data["id"]
                    if q_id not in answers or not answers[q_id]:
                        all_answered = False
                        break
                
                if all_answered:
                    # Generate feature recommendations based on answers
                    st.info("🤖 Analyzing your requirements and generating feature recommendations...")
                    
                    try:
                        must_have, competitor_suggestions = generate_feature_recommendations(
                            page_type_key=st.session_state.page_type_key,
                            questionnaire_answers=answers,
                            page_type_config=st.session_state.page_type_config
                        )
                        
                        # Store in session state
                        st.session_state.must_have_features = must_have
                        st.session_state.competitor_suggestions = competitor_suggestions
                        
                        # Display recommendations
                        st.success("✅ Feature recommendations generated!")
                        
                        with st.expander("📋 Must-Have Features (will be included)", expanded=True):
                            if must_have.get("features"):
                                for i, feature in enumerate(must_have["features"], 1):
                                    st.markdown(f"{i}. **{feature}**")
                                if must_have.get("explanation"):
                                    st.caption(f"💡 {must_have['explanation']}")
                            else:
                                st.info("No specific must-have features identified.")
                        
                        with st.expander("💡 Competitor Feature Suggestions (consider adding)", expanded=False):
                            if competitor_suggestions.get("suggestions"):
                                for i, suggestion in enumerate(competitor_suggestions["suggestions"], 1):
                                    st.markdown(f"{i}. **{suggestion}**")
                                if competitor_suggestions.get("explanation"):
                                    st.caption(f"💡 {competitor_suggestions['explanation']}")
                            else:
                                st.info("No competitor suggestions available.")
                        
                        # Emit chat message indicating questionnaire completion
                        emitter.emit_chat_message("Thank you for providing the information. I've analyzed your requirements and generated feature recommendations.")
                    except Exception as e:
                        st.warning(f"⚠️ Could not generate feature recommendations: {e}")
                        st.session_state.must_have_features = {}
                        st.session_state.competitor_suggestions = {}
                        emitter.emit_chat_message("Thank you for providing the information. I'll now proceed with generating your webpage.")
                    
                    # Emit stream complete to resume flow
                    emitter.emit_stream_complete()
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("Please answer all questions before continuing.")
    else:
        # No questionnaire available, skip to next step
        st.session_state.step = 1
        st.rerun()

# --------------------------------------------------
# STEP 1 — WIZARD MODE
# --------------------------------------------------
if st.session_state.step == 1:
    st.subheader("Wizard Mode")
    
    # Display detected page type
    page_type_config = st.session_state.page_type_config
    if page_type_config:
        st.success(f"✨ **Detected Page Type:** {page_type_config['name']}")
        st.info(f"**Category:** {page_type_config['category']}")
        
        with st.expander("📋 View Expected Features & Components"):
            st.markdown("**Core Pages:**")
            for page in page_type_config['core_pages']:
                st.markdown(f"- {page}")
            
            st.markdown("\n**Components:**")
            for component in page_type_config['components']:
                st.markdown(f"- **{component['name']}**: {component['description']}")

    st.session_state.wizard_mode = st.radio(
        "Choose input method:",
        ["manual", "default (AI-recommended)"]
    )

    if st.button("Next"):
        st.session_state.step = 2
        st.rerun()

# --------------------------------------------------
# STEP 2 — WIZARD INPUTS
# --------------------------------------------------
if st.session_state.step == 2:
    st.subheader("Page Details")

    # Display detected page type prominently
    page_type_config = st.session_state.page_type_config
    if page_type_config:
        st.success(f"🎯 **Building:** {page_type_config['name']} ({page_type_config['category']})")
        
        # Show questionnaire answers if available
        questionnaire_answers = st.session_state.questionnaire_answers
        if questionnaire_answers:
            with st.expander("✅ Your Requirements (from questionnaire)", expanded=False):
                for key, value in questionnaire_answers.items():
                    if isinstance(value, list) and value:
                        st.markdown(f"**{key.replace('_', ' ').title()}:** {', '.join(value)}")
                    elif value:
                        st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # Show components that will be included
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("📄 Core Pages to be Generated", expanded=False):
                for i, page in enumerate(page_type_config['core_pages'], 1):
                    st.markdown(f"{i}. {page}")
        
        with col2:
            with st.expander("🧩 Components to be Included", expanded=True):
                for component in page_type_config['components']:
                    st.markdown(f"**{component['name']}**")
                    st.caption(component['description'])
                    st.markdown("---")
        
        st.info("💡 These features will be automatically included in your generated project")
    
    c = st.session_state.collected

    # AI DEFAULTS
    if st.session_state.wizard_mode.startswith("default") and not c:
        prompt = f"Return JSON only. Keys: hero_text, subtext, cta, theme.\nUser intent: {st.session_state.history['initial_query']}"
        try:
            # Use smaller model for simple defaults generation
            smaller_model = get_smaller_model()
            print(f"[WIZARD_DEFAULTS] Using model: {smaller_model}")
            defaults = json.loads(generate_text(prompt, model=smaller_model))
            if isinstance(defaults, dict):
                c.update(defaults)
        except Exception:
            pass

    c["hero_text"] = st.text_input("Hero text", c.get("hero_text", ""))
    c["subtext"] = st.text_input("Subtext", c.get("subtext", ""))
    c["cta"] = st.text_input("CTA", c.get("cta", "Get Started"))

    c["theme"] = st.selectbox(
        "Theme",
        THEMES,
        index=safe_theme_index(c.get("theme"))
    )
    
    # Show generation summary
    if page_type_config:
        st.markdown("---")
        st.markdown("### 📦 What will be generated:")
        
        components_list = ", ".join([comp['name'] for comp in page_type_config['components']])
        pages_count = len(page_type_config['core_pages'])
        components_count = len(page_type_config['components'])
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Page Type", page_type_config['name'])
        with col_b:
            st.metric("Core Pages", pages_count)
        with col_c:
            st.metric("Components", components_count)
        
        st.caption(f"✅ Includes: {components_list}")

    if st.button("Generate Project"):
        st.session_state.history["wizard_inputs"] = dict(c)
        st.session_state.step = 3
        st.rerun()

# --------------------------------------------------
# STEP 3 — GENERATE LOVABLE JSON
# --------------------------------------------------
if st.session_state.step == 3:
    st.subheader("Generating project.json")
    
    # Initialize event system (reuse from questionnaire if available)
    event_logger = get_event_logger()
    if hasattr(st.session_state, 'project_id') and hasattr(st.session_state, 'conversation_id'):
        # Reuse IDs from questionnaire step
        project_id = st.session_state.project_id
        conversation_id = st.session_state.conversation_id
        # Reuse emitter if available, otherwise create new one
        if hasattr(st.session_state, 'questionnaire_emitter') and st.session_state.questionnaire_emitter:
            emitter = st.session_state.questionnaire_emitter
        else:
            emitter = EventEmitter(
                project_id=project_id,
                conversation_id=conversation_id,
                callback=lambda event: event_logger.log_event(event)
            )
    else:
        # Create new IDs if questionnaire wasn't used
        project_id = f"proj_{int(time.time())}"
        conversation_id = f"conv_{int(time.time())}"
        emitter = EventEmitter(
            project_id=project_id,
            conversation_id=conversation_id,
            callback=lambda event: event_logger.log_event(event)
        )
    
    # Emit initial events
    emitter.emit_chat_message("Starting project generation...")
    
    # Show progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.info("🔄 Preparing generation prompt...")
    progress_bar.progress(10)
    emitter.emit_progress_init(
        steps=[
            {"id": "prepare", "label": "Preparing", "status": "in_progress"},
            {"id": "generate", "label": "Generating", "status": "pending"},
            {"id": "parse", "label": "Parsing", "status": "pending"},
            {"id": "save", "label": "Saving", "status": "pending"},
        ],
        mode="inline"
    )
    
    # Build the prompt with page-specific features
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
    page_type_config = st.session_state.page_type_config
    if page_type_config:
        status_text.info(f"📋 Configuring {page_type_config['name']} requirements...")
        progress_bar.progress(20)
        emitter.emit_chat_message(f"Configuring {page_type_config['name']} requirements...")
        
        base_prompt += f"\n=== PAGE TYPE: {page_type_config['name']} ({page_type_config['category']}) ===\n"
        base_prompt += f"Target User: {page_type_config['end_user']}\n\n"
        
        base_prompt += "REQUIRED CORE PAGES:\n"
        for i, page in enumerate(page_type_config['core_pages'], 1):
            base_prompt += f"{i}. {page}\n"
        
        base_prompt += "\n\nREQUIRED COMPONENTS TO IMPLEMENT:\n"
        for i, component in enumerate(page_type_config['components'], 1):
            base_prompt += f"{i}. **{component['name']}**: {component['description']}\n"
        
        # Make Auth Module optional/simplified for faster development
        # Users can add full auth later if needed
        if "Auth Module" in page_type_config.get('core_pages', []):
            base_prompt += "\n\nAUTHENTICATION NOTE:\n"
            base_prompt += "- For 'Auth Module', create a SIMPLE login page (no backend required)\n"
            base_prompt += "- Use mock authentication (hardcoded credentials or localStorage)\n"
            base_prompt += "- Focus on the UI/UX, not complex auth flows\n"
            base_prompt += "- The main app should be accessible after simple login\n"
            base_prompt += "- Skip complex features like password reset, email verification, OAuth for now\n\n"
        
        base_prompt += "\n\nIMPORTANT: Implement ALL core pages and components. Each must be fully functional React components with TypeScript. Include proper routing.\n\n"
        
        # Only add relevant requirements based on page type (optimize prompt length)
        if page_type_config['category'] in ['ecommerce', 'marketplace']:
            base_prompt += "CRITICAL: Include product images, galleries, and proper image handling.\n\n"
        elif page_type_config['category'] in ['business', 'service']:
            base_prompt += "CRITICAL: Include contact forms, business details, and proper navigation.\n\n"
    
    # Add questionnaire answers if available
    questionnaire_answers = st.session_state.questionnaire_answers
    if questionnaire_answers:
        status_text.info("📝 Adding user requirements from questionnaire...")
        progress_bar.progress(30)
        base_prompt += "\n=== USER REQUIREMENTS (from questionnaire) ===\n"
        
        # Get questionnaire to map question IDs to question text for better context
        questionnaire = get_questionnaire(st.session_state.page_type_key) if hasattr(st.session_state, 'page_type_key') else None
        question_map = {}
        if questionnaire:
            for q in questionnaire.get("questions", []):
                question_map[q["id"]] = q.get("question", q["id"])
        
        for key, value in questionnaire_answers.items():
            # Include question context if available
            question_text = question_map.get(key, key)
            if isinstance(value, list):
                # For multiselect, show all selected options with context
                formatted_value = ', '.join(value)
                base_prompt += f"- {question_text}\n  Selected: {formatted_value}\n"
            else:
                # For radio/single select, show the selected option with context
                base_prompt += f"- {question_text}\n  Answer: {value}\n"
        
        base_prompt += "\nIMPORTANT: Use these specific requirements to tailor the design, content, features, and functionality. Each requirement should be reflected in the generated code and UI.\n\n"
    
    # Add must-have features and competitor suggestions
    if hasattr(st.session_state, 'must_have_features') and st.session_state.must_have_features:
        must_have = st.session_state.must_have_features
        if must_have.get("features"):
            base_prompt += "\n=== MUST-HAVE FEATURES (based on questionnaire answers) ===\n"
            for feature in must_have["features"]:
                base_prompt += f"- {feature}\n"
            if must_have.get("explanation"):
                base_prompt += f"\nExplanation: {must_have['explanation']}\n"
            base_prompt += "\nCRITICAL: All must-have features listed above MUST be implemented in the generated project. These are non-negotiable requirements derived from the user's questionnaire answers.\n\n"

    if hasattr(st.session_state, 'competitor_suggestions') and st.session_state.competitor_suggestions:
        competitor = st.session_state.competitor_suggestions
        if competitor.get("suggestions"):
            base_prompt += "\n=== COMPETITOR FEATURE SUGGESTIONS (consider implementing) ===\n"
            for suggestion in competitor["suggestions"]:
                base_prompt += f"- {suggestion}\n"
            if competitor.get("explanation"):
                base_prompt += f"\nExplanation: {competitor['explanation']}\n"
            base_prompt += "\nNOTE: These are industry-standard features that successful competitors use. Consider implementing them if they align with the project goals and enhance user experience.\n\n"
    
    final_prompt = base_prompt + "USER_FIELDS:\n" + json.dumps(st.session_state.collected, ensure_ascii=False)
    
    # For FIRST TIME generation, always use gemini-3-pro-preview regardless of complexity
    # This ensures high quality output for all initial generations
    webpage_model = "gemini-3-pro-preview"
    
    # Determine estimated time based on page type complexity
    complex_page_types = ['crm_dashboard', 'hr_portal', 'inventory_management', 'ai_tutor_lms']
    medium_page_types = ['ecommerce', 'ecommerce_fashion', 'service_marketplace', 'hyperlocal_delivery', 'real_estate_listing']
    simple_page_types = ['landing_page', 'student_portfolio', 'digital_product_store', 'generic']
    
    page_type_key = st.session_state.page_type_key if hasattr(st.session_state, 'page_type_key') else None
    
    # Estimate time based on complexity (but always use gemini-3-pro-preview for first generation)
    if page_type_key in complex_page_types:
        estimated_time = "90-150 seconds"
        model_reason = "complex dashboard (many components & pages) - using gemini-3-pro-preview for best quality"
    elif page_type_key in medium_page_types:
        estimated_time = "60-100 seconds"
        model_reason = "moderate complexity - using gemini-3-pro-preview for best quality"
    else:
        estimated_time = "40-80 seconds"
        model_reason = "simpler page structure - using gemini-3-pro-preview for best quality"
    
    print(f"[WEBPAGE_GENERATION] Using model: {webpage_model} (FIRST TIME - always gemini-3-pro-preview)")
    print(f"[WEBPAGE_GENERATION] Intent: webpage_build")
    print(f"[WEBPAGE_GENERATION] Page type: {page_type_key}")
    print(f"[WEBPAGE_GENERATION] Prompt length: {len(final_prompt)} characters")
    
    status_text.info(f"🤖 **Generating webpage** using model: **{webpage_model}** (First generation - always using best model)")
    status_text.info(f"⏳ Estimated time: **{estimated_time}** ({model_reason})")
    if page_type_key in complex_page_types:
        with st.expander("ℹ️ Why is this taking time?", expanded=True):
            st.markdown("""
            **CRM Dashboards are complex by nature:**
            - 📊 Multiple dashboard views (overview, analytics, reports)
            - 👥 Contact & lead management pages
            - 💼 Deal/pipeline tracking
            - 📅 Calendar & scheduling (even basic version)
            - 📝 Task management
            - ⚙️ Settings & configuration pages
            - 🔐 Authentication & user management
            
            **The model is generating:**
            - 15-25+ React components
            - 8-12+ page routes
            - TypeScript types & interfaces
            - State management setup
            - API integration stubs
            - Styling & responsive layouts
            
            **This is normal!** Even without calendar integration, a functional CRM requires significant code.
            """)
    progress_bar.progress(40)
    
    start_time = time.time()
    emitter.emit_progress_update("prepare", "completed")
    emitter.emit_progress_update("generate", "in_progress")
    emitter.emit_thinking_start()
    
    # No fallback models needed for first generation - we're using the best model
    fallback_models = None
    
    try:
        emitter.emit_chat_message(f"Generating project using {webpage_model}...")
        output = generate_text(final_prompt, model=webpage_model, fallback_models=fallback_models)
        elapsed_time = time.time() - start_time
        emitter.emit_thinking_end(duration_ms=int(elapsed_time * 1000))
        emitter.emit_progress_update("generate", "completed")
        emitter.emit_progress_update("parse", "in_progress")
        print(f"[WEBPAGE_GENERATION] Generation completed in {elapsed_time:.2f} seconds")
        print(f"[WEBPAGE_GENERATION] Output length: {len(output)} characters")
        print(f"[WEBPAGE_GENERATION] Output preview (first 500 chars): {output[:500]}")
        
        # Show timing feedback
        if elapsed_time > 90:
            status_text.warning(f"⏱️ Generation took {elapsed_time:.1f}s - this is normal for complex projects")
        else:
            status_text.success(f"⚡ Generation completed in {elapsed_time:.1f} seconds")
        
        emitter.emit_chat_message(f"Generation completed in {elapsed_time:.1f} seconds. Parsing JSON structure...")
        status_text.info("✅ Parsing JSON structure...")
        progress_bar.progress(75)
        
        # Check if output is empty or too short
        if not output or len(output) < 100:
            status_text.error("❌ Model returned empty or very short output")
            st.error("❌ Model returned empty or very short output")
            st.code(output)
            st.stop()
        
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
            status_text.error("❌ Failed to parse JSON from model output")
            progress_bar.progress(0)
            st.error("❌ Failed to parse JSON from model output")
            st.warning("The model may have returned invalid JSON or non-JSON content.")
            
            # Try to show the error location if available
            try:
                from models.json_parser import get_json_error_context, extract_json_from_text
                json_str = extract_json_from_text(output) or output
                # Try to parse to get error position
                import json as json_lib
                try:
                    json_lib.loads(json_str)
                except json_lib.JSONDecodeError as e:
                    error_context = get_json_error_context(json_str, e.pos if hasattr(e, 'pos') and e.pos else 0, context_size=300)
                    with st.expander("🔍 JSON Error Details", expanded=True):
                        st.code(error_context)
            except Exception:
                pass
            
            with st.expander("View raw output (first 3000 chars)", expanded=False):
                st.code(output[:3000] if len(output) > 3000 else output)
            
            with st.expander("View full raw output", expanded=False):
                st.code(output)
            
            st.info("💡 **Tip:** The system tried multiple recovery strategies but couldn't fix the JSON. You can try regenerating or check the raw output above.")
            event_logger.display_events()
            st.stop()
        
        emitter.emit_progress_update("parse", "completed")
        emitter.emit_progress_update("save", "in_progress")
        emitter.emit_chat_message(f"JSON parsed successfully. Project has {len(project.get('files', {}))} files.")
        print(f"[WEBPAGE_GENERATION] JSON parsed successfully")
        print(f"[WEBPAGE_GENERATION] Project has {len(project.get('files', {}))} files")
        
    except Exception as e:
        error_msg = str(e)
        status_text.error(f"❌ Error during generation: {e}")
        progress_bar.progress(0)
        
        # Check for rate limit error (429)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Rate limit" in error_msg:
            st.error("⚠️ **Rate Limit Exceeded**")
            st.warning("""
            The API quota has been exhausted during project generation. 
            
            **What happened:**
            - The system automatically retried with exponential backoff (2s, 4s, 8s delays)
            - All retry attempts failed due to quota exhaustion
            
            **Solutions:**
            1. Wait 2-5 minutes and try again
            2. Check your Vertex AI quota limits in Google Cloud Console
            3. Consider upgrading your quota if you're hitting limits frequently
            4. Try generating during off-peak hours
            
            The system will automatically retry on the next attempt.
            """)
        else:
            st.error(f"❌ Error: {e}")
            import traceback
            st.code(traceback.format_exc())
        st.stop()

    # Validation already done above, but double-check
    if not project:
        status_text.error("❌ Invalid project structure")
        progress_bar.progress(0)
        st.error("❌ Invalid project structure")
        st.stop()

    status_text.info("💾 Saving project files...")
    progress_bar.progress(85)
    emitter.emit_chat_message("Saving project files...")
    
    try:
        print(f"[WEBPAGE_GENERATION] Writing project.json...")
        emitter.emit_fs_write(
            path="project.json",
            kind="file",
            language="json",
            content=json.dumps({"project": project}, indent=2)
        )
        project_json_path = f"{OUTPUT_DIR}/project.json"
        with open(project_json_path, "w") as f:
            json.dump({"project": project}, f, indent=2)
        print(f"[WEBPAGE_GENERATION] project.json saved")
        
        progress_bar.progress(90)
        status_text.info(f"💾 Saving {len(project.get('files', {}))} files to disk...")
        emitter.emit_chat_message(f"Saving {len(project.get('files', {}))} files to disk...")
        
        save_start = time.time()
        # Emit filesystem events for each file
        files = project.get('files', {})
        for file_path, file_content in files.items():
            if isinstance(file_content, dict):
                content = file_content.get('content', '')
                language = file_content.get('language', None)
            else:
                content = file_content
                language = None
            
            # Determine language from file extension if not provided
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
        save_time = time.time() - save_start
        print(f"[WEBPAGE_GENERATION] Files saved in {save_time:.2f} seconds")
        
    except Exception as e:
        status_text.error(f"❌ Error saving files: {e}")
        progress_bar.progress(0)
        st.error(f"❌ Error saving files: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()

    progress_bar.progress(100)
    emitter.emit_progress_update("save", "completed")
    emitter.emit_chat_message("Base project generated successfully!")
    emitter.emit_stream_complete()
    status_text.success("✅ Base project generated successfully!")
    
    # Show summary
    if page_type_config:
        st.success(f"✨ Generated **{page_type_config['name']}** with {len(page_type_config.get('core_pages', []))} pages and {len(page_type_config.get('components', []))} components")
    
    # Display events for frontend/backend teams
    st.markdown("---")
    st.markdown("### 📡 Events Generated")
    st.info(f"✅ **{len(event_logger.get_events())} events** were generated during this process. See details below.")
    event_logger.display_events()
    
    # Show a note about events file
    if os.path.exists(f"{OUTPUT_DIR}/events.jsonl"):
        st.info(f"💾 All events are also saved to `{OUTPUT_DIR}/events.jsonl` for frontend/backend teams to use.")
    
    if st.button("Continue to Modification", type="primary"):
        st.session_state.step = 4
        st.rerun()

# --------------------------------------------------
# STEP 4 — MODIFICATION LOOP (INFINITE)
# --------------------------------------------------
if st.session_state.step == 4:
    st.subheader("Modify your project")

    base_path, base_project = get_latest_project()
    st.caption(f"Editing from: `{base_path}`")

    st.code(base_project, language="json")

    instruction = st.text_area("Describe modification")

    if st.button("Apply Modification"):
        # Classify modification complexity
        complexity, complexity_meta = classify_modification_complexity(instruction)
        print(f"[MODIFICATION] Complexity classification: {complexity}")
        print(f"[MODIFICATION] Complexity explanation: {complexity_meta.get('explanation', 'N/A')}")
        
        # Select model based on complexity
        mod_model = get_model_for_complexity(complexity)
        print(f"[MODIFICATION] Selected model: {mod_model} for complexity: {complexity}")
        
        # Display modification classification and model selection
        st.info(f"🔧 **Modification Complexity:** {complexity.upper()} | Model: **{mod_model}** | Confidence: {complexity_meta.get('confidence', 0.0):.2f}")
        st.caption(f"Explanation: {complexity_meta.get('explanation', 'N/A')}")
        
        mod_prompt = f"""Modify project JSON. Return JSON only: {{"project": {{...}}}}. Match base schema. Change ONLY requested parts, keep rest unchanged. NO markdown/code blocks/explanations. Raw JSON only.

Base: {json.dumps({"project": base_project}, indent=2)}
Request: {instruction}"""

        # Try with the selected model first
        mod_out = None
        mod_project = None
        
        try:
            mod_out = generate_text(mod_prompt, model=mod_model)
            mod_project = parse_project_json(mod_out)
        except Exception as e:
            error_msg = str(e)
            print(f"[MODIFICATION] Error with model {mod_model}: {e}")
            
            # Check for rate limit error (429)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Rate limit" in error_msg:
                st.error("⚠️ **Rate Limit Exceeded**")
                st.warning("""
                The API quota has been exhausted. This usually happens when:
                - Too many requests were made in a short time
                - The daily/monthly quota limit has been reached
                
                **Solutions:**
                1. Wait 1-2 minutes and try again (the system will automatically retry)
                2. Check your Vertex AI quota limits in Google Cloud Console
                3. Consider upgrading your quota if needed
                
                The system has already attempted automatic retries with exponential backoff.
                """)
                st.stop()
        
        # If parsing failed and we used a smaller model, retry with gemini-3-pro-preview
        if not mod_project and mod_model != "gemini-3-pro-preview":
            print(f"[MODIFICATION] Retrying with gemini-3-pro-preview due to invalid output")
            st.warning(f"⚠️ Retrying with gemini-3-pro-preview for better JSON output...")
            try:
                mod_out = generate_text(mod_prompt, model="gemini-3-pro-preview")
                mod_project = parse_project_json(mod_out)
            except Exception as e:
                error_msg = str(e)
                print(f"[MODIFICATION] Error with fallback model: {e}")
                
                # Check for rate limit error in fallback
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Rate limit" in error_msg:
                    st.error("⚠️ **Rate Limit Exceeded**")
                    st.warning("""
                    The API quota has been exhausted even after retries. 
                    
                    **Please:**
                    1. Wait 2-5 minutes before trying again
                    2. Check your Vertex AI quota limits in Google Cloud Console
                    3. Consider reducing the frequency of requests
                    """)
                    st.stop()

        if not mod_project:
            st.error("❌ Invalid modification output - model did not return valid JSON")
            st.error("The model returned non-JSON content. Please try:")
            st.markdown("1. Be more specific in your modification request")
            st.markdown("2. The system will automatically retry with a more capable model")
            if mod_out:
                with st.expander("View raw output (for debugging)"):
                    st.code(mod_out[:2000] if len(mod_out) > 2000 else mod_out)
            st.stop()

        # Validate that mod_project has the required structure
        if not isinstance(mod_project, dict):
            st.error("❌ Invalid project structure: expected dict")
            st.stop()
        
        if "files" not in mod_project:
            st.error("❌ Invalid project structure: missing 'files' key")
            st.stop()

        # Save the modified project
        try:
            version = f"project_{int(time.time())}"
            dest = os.path.join(MODIFIED_DIR, version)
            os.makedirs(dest, exist_ok=True)

            project_json_path = os.path.join(dest, "project.json")
            with open(project_json_path, "w") as f:
                json.dump({"project": mod_project}, f, indent=2)

            save_project_files(mod_project, os.path.join(dest, "project"))

            st.session_state.history["modifications"].append({
                "instruction": instruction,
                "from": base_path,
                "to": dest,
            })

            st.success(f"✅ **Modification saved successfully!**")
            st.info(f"📁 **Location:** `{dest}`")
            st.info(f"📄 **Project JSON:** `{project_json_path}`")
            
            # Update the last project path so next modification uses this one
            st.session_state.last_project_path = project_json_path
            
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error saving modification: {e}")
            st.exception(e)
            st.stop()