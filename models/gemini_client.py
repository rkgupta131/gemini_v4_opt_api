# models/gemini_client.py
import os
import json
import re
import time
from typing import Optional, Tuple, Generator

from google import genai
from google.genai.types import HttpOptions

# --------------------------------------------------
# Lazy client creation (CRITICAL for Streamlit)
# --------------------------------------------------

_client = None

def _make_client():
    global _client
    if _client is not None:
        return _client

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

    if not project:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is not set. "
            "Make sure load_dotenv() is called in app.py BEFORE importing gemini_client."
        )

    _client = genai.Client(
        vertexai=True,
        project=project,
        location=location,
        http_options=HttpOptions(api_version="v1"),
    )
    return _client


# --------------------------------------------------
# Text generation
# --------------------------------------------------

def generate_text(prompt: str, model: str = "gemini-3-pro-preview", fallback_models: list = None, max_retries: int = 3) -> str:
    """
    Generates text using the specified model with retry logic for rate limits.
    Default is gemini-3-pro-preview for webpage building.
    
    If the model fails and fallback_models is provided, tries those in order.
    Automatically retries on 429 (rate limit) errors with exponential backoff.
    """
    client = _make_client()
    
    models_to_try = [model]
    if fallback_models:
        models_to_try.extend(fallback_models)
    
    last_error = None
    last_error_code = None
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if model_name != model:
                    print(f"[MODEL_FALLBACK] ✅ Used fallback model: {model_name} (original: {model})")
                return getattr(resp, "text", "") or str(resp)
            except Exception as e:
                error_msg = str(e)
                
                # Check for 429 error (rate limit / resource exhausted)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Resource exhausted" in error_msg:
                    last_error_code = 429
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2^attempt seconds (2s, 4s, 8s)
                        wait_time = 2 ** attempt
                        print(f"[RATE_LIMIT] ⚠️ Rate limit hit (429). Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Last attempt failed
                        print(f"[RATE_LIMIT] ❌ Rate limit exceeded after {max_retries} attempts")
                        last_error = e
                        break
                
                # Check for 404 error (model not found)
                elif "404" in error_msg or "NOT_FOUND" in error_msg:
                    last_error_code = 404
                    if model_name != models_to_try[-1]:
                        print(f"[MODEL_FALLBACK] ⚠️ Model {model_name} not available (404), trying next fallback...")
                        last_error = e
                        break
                    else:
                        print(f"[MODEL_FALLBACK] ❌ All models failed. Last attempted: {model_name}")
                        print(f"[MODEL_FALLBACK] 💡 Tip: Check Vertex AI model availability in your region/project")
                        raise e
                
                # Other errors - don't retry, just move to next model or raise
                else:
                    last_error = e
                    last_error_code = None
                    if model_name != models_to_try[-1]:
                        # Try next model
                        break
                    else:
                        # Last model, raise error
                        raise e
        
        # If we broke out of retry loop due to 429, continue to next model or raise
        if last_error and last_error_code == 429 and model_name == models_to_try[-1]:
            # Last model failed with 429, raise with helpful message
            raise RuntimeError(
                "Rate limit exceeded (429). The API quota has been exhausted. "
                "Please wait a few minutes and try again. "
                "If this persists, check your Vertex AI quota limits in Google Cloud Console."
            ) from last_error
    
    # Handle 429 error with user-friendly message
    if last_error:
        error_msg = str(last_error)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "Rate limit" in error_msg:
            raise RuntimeError(
                "Rate limit exceeded (429). The API quota has been exhausted. "
                "Please wait a few minutes and try again. "
                "If this persists, check your Vertex AI quota limits in Google Cloud Console."
            ) from last_error
        raise last_error
    
    raise RuntimeError("No models available")


def generate_stream(prompt: str, model: str = "gemini-3-pro-preview") -> Generator[str, None, None]:
    """
    Generates streaming text using the specified model.
    Default is gemini-3-pro-preview for webpage building.
    """
    client = _make_client()

    if hasattr(client.models, "generate_content_stream"):
        for part in client.models.generate_content_stream(
            model=model,
            contents=prompt,
        ):
            if hasattr(part, "text") and part.text:
                yield part.text
    else:
        yield generate_text(prompt, model=model)


# --------------------------------------------------
# Intent classification
# --------------------------------------------------

def classify_intent(user_text: str, model: str = None) -> Tuple[str, dict]:
    """
    Classifies user intent using a smaller model for efficiency.
    Returns: (label, metadata)
    """
    if model is None:
        model = get_smaller_model()
    
    instructions = (
        "Classify intent. Return JSON only:\n"
        '{ "label": "webpage_build|greeting_only|chat|illegal|other", "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "webpage_build=wants webpage; greeting_only=hello; chat=Q/A; illegal=disallowed; other=else. Treat 'what is webpage' as chat."
    )
    prompt = instructions + "\n\nUser message:\n" + json.dumps(user_text)
    
    print(f"[INTENT_CLASSIFICATION] Using model: {model}")
    print(f"[INTENT_CLASSIFICATION] User query: {user_text[:100]}...")
    
    # Fallback models if primary fails (try flash, then pro-preview)
    fallback_models = ["gemini-2.0-flash", "gemini-3-pro-preview"]
    
    try:
        out = generate_text(prompt, model=model, fallback_models=fallback_models)
        # extract first JSON object
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            cand = out[start:end+1]
            parsed = json.loads(cand)
            label = parsed.get("label", "chat")
            explanation = parsed.get("explanation", "")
            try:
                confidence = float(parsed.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            
            result = {"explanation": explanation, "confidence": confidence, "raw": out, "model": model}
            print(f"[INTENT_CLASSIFICATION] Result: label={label}, confidence={confidence:.2f}, explanation={explanation}")
            return label, result
        result = {"explanation": "Could not parse classifier output", "confidence": 0.0, "raw": out, "model": model}
        print(f"[INTENT_CLASSIFICATION] Result: label=chat (fallback), confidence=0.0")
        return "chat", result
    except Exception as e:
        result = {"explanation": f"classifier error: {e}", "confidence": 0.0, "raw": "", "model": model}
        print(f"[INTENT_CLASSIFICATION] Error: {e}")
        return "chat", result

# --------------------------------------------------
# Page Type Classification
# --------------------------------------------------

def classify_page_type(user_text: str, model: str = None) -> Tuple[str, dict]:
    """
    Classifies the page type based on user input using a smaller model.
    Returns: (page_type_key, metadata)
    
    Possible page types:
    - landing_page
    - crm_dashboard
    - hr_portal
    - inventory_management
    - ecommerce
    - ecommerce_fashion
    - digital_product_store
    - service_marketplace
    - student_portfolio
    - hyperlocal_delivery
    - real_estate_listing
    - ai_tutor_lms
    - generic (fallback)
    """
    instructions = (
        "Classify page type. Return JSON only:\n"
        '{ "page_type": "landing_page|crm_dashboard|hr_portal|inventory_management|ecommerce|ecommerce_fashion|digital_product_store|service_marketplace|student_portfolio|hyperlocal_delivery|real_estate_listing|ai_tutor_lms|generic", "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "Types: landing_page=marketing/lead capture; crm_dashboard=CRM/sales; hr_portal=HR/employees; inventory_management=stock/warehouse; ecommerce=general store (NOT fashion); ecommerce_fashion=clothing/apparel ONLY; digital_product_store=downloads/templates; service_marketplace=two-sided/booking; student_portfolio=resume/showcase; hyperlocal_delivery=food/grocery; real_estate_listing=properties; ai_tutor_lms=learning/courses; generic=fallback.\n"
        "Use ecommerce_fashion ONLY if user mentions fashion/clothing/apparel."
    )
    prompt = instructions + "\n\nUser message:\n" + json.dumps(user_text)
    
    if model is None:
        model = get_smaller_model()
    
    print(f"[PAGE_TYPE_CLASSIFICATION] Using model: {model}")
    
    # Fallback models if primary fails (try flash, then pro-preview)
    fallback_models = ["gemini-2.0-flash", "gemini-3-pro-preview"]
    
    try:
        out = generate_text(prompt, model=model, fallback_models=fallback_models)
        # extract first JSON object
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            cand = out[start:end+1]
            parsed = json.loads(cand)
            page_type = parsed.get("page_type", "generic")
            explanation = parsed.get("explanation", "")
            try:
                confidence = float(parsed.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            result = {"explanation": explanation, "confidence": confidence, "raw": out, "model": model}
            print(f"[PAGE_TYPE_CLASSIFICATION] Result: page_type={page_type}, confidence={confidence:.2f}")
            return page_type, result
        result = {"explanation": "Could not parse classifier output", "confidence": 0.0, "raw": out, "model": model}
        print(f"[PAGE_TYPE_CLASSIFICATION] Result: page_type=generic (fallback)")
        return "generic", result
    except Exception as e:
        result = {"explanation": f"classifier error: {e}", "confidence": 0.0, "raw": "", "model": model}
        print(f"[PAGE_TYPE_CLASSIFICATION] Error: {e}")
        return "generic", result


# --------------------------------------------------
# Query Detail Analysis
# --------------------------------------------------

def analyze_query_detail(user_text: str, model: str = None) -> Tuple[bool, float]:
    """
    Analyzes if the user query has enough detail or needs follow-up questions using a smaller model.
    Returns: (needs_followup, confidence_score)
    
    If needs_followup=True, the app should show MCQ questionnaire.
    If needs_followup=False, the query is detailed enough to proceed.
    """
    instructions = (
        "Analyze if request needs follow-up. Return JSON only:\n"
        '{ "needs_followup": true/false, "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "true=vague ('build CRM'); false=specific ('landing page for SaaS targeting developers with pricing'). Check: industry, audience, features, purpose."
    )
    prompt = instructions + "\n\nUser request:\n" + json.dumps(user_text)
    
    if model is None:
        model = get_smaller_model()
    
    print(f"[QUERY_DETAIL_ANALYSIS] Using model: {model}")
    
    # Fallback models if primary fails (try flash, then pro-preview)
    fallback_models = ["gemini-2.0-flash", "gemini-3-pro-preview"]
    
    try:
        out = generate_text(prompt, model=model, fallback_models=fallback_models)
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            cand = out[start:end+1]
            parsed = json.loads(cand)
            needs_followup = parsed.get("needs_followup", True)
            explanation = parsed.get("explanation", "")
            try:
                confidence = float(parsed.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            print(f"[QUERY_DETAIL_ANALYSIS] Result: needs_followup={needs_followup}, confidence={confidence:.2f}")
            return needs_followup, confidence
        print(f"[QUERY_DETAIL_ANALYSIS] Result: needs_followup=True (fallback)")
        return True, 0.0  # Default to showing questions if unclear
    except Exception as e:
        print(f"[QUERY_DETAIL_ANALYSIS] Error: {e}")
        return True, 0.0  # Default to showing questions on error


# --------------------------------------------------
# Feature Recommendations Generation
# --------------------------------------------------

def generate_feature_recommendations(
    page_type_key: str,
    questionnaire_answers: dict,
    page_type_config: dict = None,
    model: str = None
) -> Tuple[dict, dict]:
    """
    Generates must-have features and competitor feature suggestions based on questionnaire answers.
    Returns: (must_have_features, competitor_suggestions)
    
    must_have_features: {
        "features": ["feature1", "feature2"],
        "explanation": "why these are must-have"
    }
    
    competitor_suggestions: {
        "suggestions": ["feature1", "feature2"],
        "explanation": "what competitors are using"
    }
    """
    if model is None:
        model = get_smaller_model()
    
    # Build context from questionnaire answers
    answers_context = ""
    for key, value in questionnaire_answers.items():
        if isinstance(value, list):
            answers_context += f"- {key}: {', '.join(value)}\n"
        else:
            answers_context += f"- {key}: {value}\n"
    
    # Build page type context
    page_context = ""
    if page_type_config:
        page_context = f"""
Page Type: {page_type_config.get('name', page_type_key)}
Category: {page_type_config.get('category', 'N/A')}
Target User: {page_type_config.get('end_user', 'N/A')}
"""
    
    instructions = (
        "Analyze requirements. Generate two lists:\n"
        "1. MUST-HAVE features (critical, from answers)\n"
        "2. Competitor suggestions (industry-standard features)\n"
        "Return JSON only: {\"must_have_features\": {\"features\": [...], \"explanation\": \"...\"}, \"competitor_suggestions\": {\"suggestions\": [...], \"explanation\": \"...\"}}\n"
        "Rules: Must-haves from answers; competitor=industry-standard; specific names (e.g., 'User Authentication'); 5-8 per category; consider page type/audience."
    )
    
    prompt = instructions + page_context + "\nQuestionnaire Answers:\n" + answers_context
    
    print(f"[FEATURE_RECOMMENDATIONS] Using model: {model}")
    print(f"[FEATURE_RECOMMENDATIONS] Page type: {page_type_key}")
    
    fallback_models = ["gemini-2.0-flash", "gemini-3-pro-preview"]
    
    try:
        out = generate_text(prompt, model=model, fallback_models=fallback_models)
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            cand = out[start:end+1]
            parsed = json.loads(cand)
            
            must_have = parsed.get("must_have_features", {})
            competitor = parsed.get("competitor_suggestions", {})
            
            result_must_have = {
                "features": must_have.get("features", []),
                "explanation": must_have.get("explanation", "")
            }
            result_competitor = {
                "suggestions": competitor.get("suggestions", []),
                "explanation": competitor.get("explanation", "")
            }
            
            print(f"[FEATURE_RECOMMENDATIONS] Generated {len(result_must_have['features'])} must-have features")
            print(f"[FEATURE_RECOMMENDATIONS] Generated {len(result_competitor['suggestions'])} competitor suggestions")
            
            return result_must_have, result_competitor
        else:
            # Fallback if JSON parsing fails
            print(f"[FEATURE_RECOMMENDATIONS] Failed to parse JSON, using fallback")
            return {"features": [], "explanation": ""}, {"suggestions": [], "explanation": ""}
    except Exception as e:
        print(f"[FEATURE_RECOMMENDATIONS] Error: {e}")
        import traceback
        print(f"[FEATURE_RECOMMENDATIONS] Traceback: {traceback.format_exc()}")
        return {"features": [], "explanation": ""}, {"suggestions": [], "explanation": ""}


# --------------------------------------------------
# Chat response (short)
# --------------------------------------------------

def chat_response(user_text: str, model: str = None) -> str:
    """
    Generates a chat response using a smaller model for simple conversations.
    """
    if model is None:
        model = get_smaller_model()
    
    prompt = f"Reply max 4 sentences.\nUser: {user_text}"
    print(f"[CHAT_RESPONSE] Using model: {model}")
    
    # Fallback models if primary fails (try flash, then pro-preview)
    fallback_models = ["gemini-2.0-flash", "gemini-3-pro-preview"]
    
    out = generate_text(prompt, model=model, fallback_models=fallback_models)
    parts = re.split(r'(?<=[.!?])\s+', out.strip())
    result = " ".join(parts[:4])
    print(f"[CHAT_RESPONSE] Generated response (length: {len(result)} chars)")
    return result


# --------------------------------------------------
# Modification Complexity Classification
# --------------------------------------------------

def classify_modification_complexity(instruction: str, model: str = None) -> Tuple[str, dict]:
    """
    Classifies the complexity of a modification request.
    Returns: (complexity_level, metadata)
    
    Complexity levels:
    - small: Simple changes (text updates, color changes, minor styling)
    - medium: Moderate changes (adding components, modifying layouts, updating features)
    - complex: Major changes (restructuring, adding multiple features, complex logic changes)
    """
    instructions = (
        "Classify modification complexity. Return JSON only:\n"
        '{ "complexity": "small|medium|complex", "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "small=text/color/CSS tweaks; medium=add component/modify layout; complex=major restructure/multiple features. Ex: 'Change title'=small, 'Add form'=medium, 'Redesign dashboard'=complex."
    )
    prompt = instructions + "\n\nModification instruction:\n" + json.dumps(instruction)
    
    if model is None:
        model = get_smaller_model()
    
    print(f"[MODIFICATION_COMPLEXITY] Using model: {model}")
    print(f"[MODIFICATION_COMPLEXITY] Instruction: {instruction[:100]}...")
    
    # Fallback models if primary fails (try flash, then pro-preview)
    fallback_models = ["gemini-2.0-flash", "gemini-3-pro-preview"]
    
    try:
        out = generate_text(prompt, model=model, fallback_models=fallback_models)
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            cand = out[start:end+1]
            parsed = json.loads(cand)
            complexity = parsed.get("complexity", "medium")
            explanation = parsed.get("explanation", "")
            try:
                confidence = float(parsed.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            
            # Ensure complexity is one of the valid values
            if complexity not in ["small", "medium", "complex"]:
                complexity = "medium"
            
            result = {"explanation": explanation, "confidence": confidence, "raw": out, "model": model}
            print(f"[MODIFICATION_COMPLEXITY] Result: complexity={complexity}, confidence={confidence:.2f}, explanation={explanation}")
            return complexity, result
        result = {"explanation": "Could not parse classifier output", "confidence": 0.0, "raw": out, "model": model}
        print(f"[MODIFICATION_COMPLEXITY] Result: complexity=medium (fallback)")
        return "medium", result
    except Exception as e:
        result = {"explanation": f"classifier error: {e}", "confidence": 0.0, "raw": "", "model": model}
        print(f"[MODIFICATION_COMPLEXITY] Error: {e}")
        return "medium", result


# --------------------------------------------------
# Model Selection Helper
# --------------------------------------------------

def get_smaller_model() -> str:
    """
    Returns a smaller/faster model for classification and simple tasks.
    Uses Gemini 2.0 models which are the current recommended models.
    """
    # Use Gemini 2.0 models (1.5 models are being retired)
    # gemini-2.0-flash-lite is the most cost-effective for simple tasks
    # gemini-2.0-flash is a good alternative
    return "gemini-2.0-flash-lite"


def get_model_for_complexity(complexity: str) -> str:
    """
    Returns the appropriate model based on complexity level.
    - small/medium: gemini-2.0-flash-lite (faster, cheaper)
    - complex: gemini-3-pro-preview (more capable)
    """
    if complexity == "complex":
        return "gemini-3-pro-preview"
    else:
        return get_smaller_model()


# --------------------------------------------------
# Lovable-style JSON parsing
# --------------------------------------------------

def parse_project_json(text: str) -> Optional[dict]:
    """
    Always returns the INNER project dict:
    {
      "name": ...,
      "files": {...}
    }
    
    Uses improved parsing with error recovery for common JSON issues.
    """
    from .json_parser import parse_json_with_fallback, get_json_error_context, extract_json_from_text
    
    if not text:
        print("[PARSE_JSON] Empty text input")
        return None

    print(f"[PARSE_JSON] Input length: {len(text)} characters")
    
    try:
        # Try to extract JSON from text (handles markdown code blocks, etc.)
        json_str = extract_json_from_text(text)
        if not json_str:
            # Fallback to simple boundary detection
            start = text.find("{")
            end = text.rfind("}")
            
            if start == -1 or end == -1:
                print(f"[PARSE_JSON] No JSON boundaries found. First 200 chars: {text[:200]}")
                return None
            json_str = text[start:end+1]
        else:
            print(f"[PARSE_JSON] Extracted JSON from code block or structured content")
        
        print(f"[PARSE_JSON] JSON string length: {len(json_str)} characters")
        print(f"[PARSE_JSON] Attempting to parse JSON...")
        
        # Try parsing with fallback strategies
        raw = parse_json_with_fallback(json_str)
        
        if raw is None:
            # If all strategies failed, try one more time with the original approach
            # to get a better error message
            try:
                raw = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"[PARSE_JSON] JSON decode error after all recovery attempts: {e}")
                error_context = get_json_error_context(json_str, e.pos, context_size=200)
                print(f"[PARSE_JSON] Error context:\n{error_context}")
                return None
        
        print(f"[PARSE_JSON] JSON parsed successfully. Type: {type(raw)}")

        # Case 1: { "project": {...} }
        if isinstance(raw, dict) and "project" in raw and isinstance(raw["project"], dict):
            print(f"[PARSE_JSON] Found 'project' key. Files count: {len(raw['project'].get('files', {}))}")
            return raw["project"]

        # Case 2: [ { "project": {...} } ]
        if isinstance(raw, list):
            print(f"[PARSE_JSON] Input is a list with {len(raw)} items")
            for item in raw:
                if isinstance(item, dict) and "project" in item:
                    print(f"[PARSE_JSON] Found 'project' in list item. Files count: {len(item['project'].get('files', {}))}")
                    return item["project"]

        # Case 3: already inner project
        if isinstance(raw, dict) and "files" in raw:
            print(f"[PARSE_JSON] Already inner project format. Files count: {len(raw.get('files', {}))}")
            return raw

        print(f"[PARSE_JSON] JSON structure doesn't match expected format. Keys: {list(raw.keys()) if isinstance(raw, dict) else 'N/A'}")

    except json.JSONDecodeError as e:
        print(f"[PARSE_JSON] JSON decode error: {e}")
        error_context = get_json_error_context(text, e.pos, context_size=200)
        print(f"[PARSE_JSON] Error context:\n{error_context}")
        return None
    except Exception as e:
        print(f"[PARSE_JSON] Unexpected error: {e}")
        import traceback
        print(f"[PARSE_JSON] Traceback: {traceback.format_exc()}")
        return None

    print("[PARSE_JSON] No matching structure found, returning None")
    return None


# --------------------------------------------------
# Save project files (STRICT)
# --------------------------------------------------

def save_project_files(project: dict, output_dir: str) -> None:
    if not isinstance(project, dict):
        raise ValueError("project must be a dict")

    files = project.get("files")
    if not isinstance(files, dict):
        raise ValueError("project.files must be a dict")

    print(f"[SAVE_FILES] Saving {len(files)} files to {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    saved_count = 0
    for rel_path, content in files.items():
        try:
            full_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            if isinstance(content, (dict, list)):
                content = json.dumps(content, indent=2)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            saved_count += 1
            if saved_count % 10 == 0:
                print(f"[SAVE_FILES] Saved {saved_count}/{len(files)} files...")
        except Exception as e:
            print(f"[SAVE_FILES] Error saving {rel_path}: {e}")
            raise
    
    print(f"[SAVE_FILES] Successfully saved {saved_count} files")

def normalize_project(project):
    """
    Ensures project is a dict with project['files'] as dict.
    Fixes common LLM output mistakes.
    """
    if isinstance(project, list):
        project = project[0]

    if "project" in project:
        project = project["project"]

    files = project.get("files")

    if isinstance(files, list):
        fixed = {}
        for item in files:
            if isinstance(item, dict):
                fixed.update(item)
        project["files"] = fixed

    if not isinstance(project.get("files"), dict):
        raise ValueError("project.files must be a dict")

    return project