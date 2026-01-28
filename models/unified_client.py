# models/unified_client.py
"""
Unified client interface for all model families.
This module provides a single interface that works with Gemini, GPT, and Claude.
"""
import json
import time
from typing import Generator, Optional, Tuple
from models.model_factory import get_provider


def generate_text(prompt: str, model: str = None, model_family: str = "gemini", 
                 fallback_models: Optional[list] = None, max_retries: int = 3) -> str:
    """
    Unified text generation across all model families.
    
    Args:
        prompt: The prompt to send to the model
        model: Specific model name (optional, uses default for family if not provided)
        model_family: "gemini", "gpt", or "claude"
        fallback_models: List of fallback models to try if primary fails
        max_retries: Maximum number of retries for rate limits
    
    Returns:
        Generated text string
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_default_model()
    
    # Convert fallback models if needed (they might be from different family)
    if fallback_models:
        # Filter fallback models to same family or convert
        family_fallbacks = []
        for fb_model in fallback_models:
            # If fallback is just a model name, assume same family
            if ":" not in fb_model:
                family_fallbacks.append(fb_model)
            elif fb_model.startswith(f"{model_family}:"):
                family_fallbacks.append(fb_model.split(":")[1])
        fallback_models = family_fallbacks if family_fallbacks else None
    
    return provider.generate_text(prompt, model, fallback_models, max_retries)


def generate_stream(prompt: str, model: str = None, model_family: str = "gemini") -> Generator[str, None, None]:
    """
    Unified streaming generation across all model families.
    
    Args:
        prompt: The prompt to send to the model
        model: Specific model name (optional, uses default for family if not provided)
        model_family: "gemini", "gpt", or "claude"
    
    Yields:
        Text chunks as they are generated
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_default_model()
    
    return provider.generate_stream(prompt, model)


def get_smaller_model(model_family: str = "gemini") -> str:
    """
    Get smaller/faster model for the specified family.
    
    Args:
        model_family: "gemini", "gpt", or "claude"
    
    Returns:
        Model name string
    """
    provider = get_provider(model_family)
    return provider.get_smaller_model()


def get_model_for_complexity(complexity: str, model_family: str = "gemini") -> str:
    """
    Get appropriate model based on task complexity for the specified family.
    
    Args:
        complexity: "low", "medium", or "high"
        model_family: "gemini", "gpt", or "claude"
    
    Returns:
        Model name string
    """
    provider = get_provider(model_family)
    return provider.get_model_for_complexity(complexity)


def classify_intent(user_text: str, model_family: str = "gemini", model: str = None) -> Tuple[str, dict]:
    """
    Classify user intent using specified model family.
    
    Args:
        user_text: User input text
        model_family: "gemini", "gpt", or "claude"
        model: Specific model name (optional)
    
    Returns:
        Tuple of (label, metadata dict)
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_smaller_model()
    
    instructions = (
        "Classify intent. Return JSON only:\n"
        '{ "label": "webpage_build|greeting_only|chat|illegal|other", "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "webpage_build=wants webpage; greeting_only=hello; chat=Q/A; illegal=disallowed; other=else. Treat 'what is webpage' as chat."
    )
    prompt = instructions + "\n\nUser message:\n" + json.dumps(user_text)
    
    print(f"[INTENT_CLASSIFICATION] Using {model_family} model: {model}")
    print(f"[INTENT_CLASSIFICATION] User query: {user_text[:100]}...")
    
    # Get fallback models for this family
    fallback_models = [provider.get_smaller_model(), provider.get_default_model()]
    
    try:
        out = provider.generate_text(prompt, model=model, fallback_models=fallback_models)
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            cand = out[start:end+1]
            parsed = json.loads(cand)
            label = parsed.get("label", "other")
            explanation = parsed.get("explanation", "")
            try:
                confidence = float(parsed.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            result = {
                "explanation": explanation,
                "confidence": confidence,
                "raw": out,
                "model": model,
                "model_family": model_family
            }
            print(f"[INTENT_CLASSIFICATION] Result: label={label}, confidence={confidence:.2f}")
            return label, result
        result = {
            "explanation": "Could not parse classifier output",
            "confidence": 0.0,
            "raw": out,
            "model": model,
            "model_family": model_family
        }
        print(f"[INTENT_CLASSIFICATION] Result: label=chat (fallback)")
        return "chat", result
    except Exception as e:
        result = {
            "explanation": f"classifier error: {e}",
            "confidence": 0.0,
            "raw": "",
            "model": model,
            "model_family": model_family
        }
        print(f"[INTENT_CLASSIFICATION] Error: {e}")
        return "chat", result


def classify_page_type(user_text: str, model_family: str = "gemini", model: str = None) -> Tuple[str, dict]:
    """
    Classify page type using specified model family.
    
    Args:
        user_text: User input text
        model_family: "gemini", "gpt", or "claude"
        model: Specific model name (optional)
    
    Returns:
        Tuple of (page_type_key, metadata dict)
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_smaller_model()
    
    instructions = (
        "Classify page type. Return JSON only:\n"
        '{ "page_type": "landing_page|crm_dashboard|hr_portal|inventory_management|ecommerce|ecommerce_fashion|digital_product_store|service_marketplace|student_portfolio|hyperlocal_delivery|real_estate_listing|ai_tutor_lms|generic", "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "Types: landing_page=marketing/lead capture; crm_dashboard=CRM/sales; hr_portal=HR/employees; inventory_management=stock/warehouse; ecommerce=general store (NOT fashion); ecommerce_fashion=clothing/apparel ONLY; digital_product_store=downloads/templates; service_marketplace=two-sided/booking; student_portfolio=resume/showcase; hyperlocal_delivery=food/grocery; real_estate_listing=properties; ai_tutor_lms=learning/courses; generic=fallback.\n"
        "Use ecommerce_fashion ONLY if user mentions fashion/clothing/apparel."
    )
    prompt = instructions + "\n\nUser message:\n" + json.dumps(user_text)
    
    print(f"[PAGE_TYPE_CLASSIFICATION] Using {model_family} model: {model}")
    
    fallback_models = [provider.get_smaller_model(), provider.get_default_model()]
    
    try:
        out = provider.generate_text(prompt, model=model, fallback_models=fallback_models)
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
            result = {
                "explanation": explanation,
                "confidence": confidence,
                "raw": out,
                "model": model,
                "model_family": model_family
            }
            print(f"[PAGE_TYPE_CLASSIFICATION] Result: page_type={page_type}, confidence={confidence:.2f}")
            return page_type, result
        result = {
            "explanation": "Could not parse classifier output",
            "confidence": 0.0,
            "raw": out,
            "model": model,
            "model_family": model_family
        }
        print(f"[PAGE_TYPE_CLASSIFICATION] Result: page_type=generic (fallback)")
        return "generic", result
    except Exception as e:
        result = {
            "explanation": f"classifier error: {e}",
            "confidence": 0.0,
            "raw": "",
            "model": model,
            "model_family": model_family
        }
        print(f"[PAGE_TYPE_CLASSIFICATION] Error: {e}")
        return "generic", result


def analyze_query_detail(user_text: str, model_family: str = "gemini", model: str = None) -> Tuple[bool, float]:
    """
    Analyze if query needs follow-up questions using specified model family.
    
    Args:
        user_text: User input text
        model_family: "gemini", "gpt", or "claude"
        model: Specific model name (optional)
    
    Returns:
        Tuple of (needs_followup: bool, confidence: float)
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_smaller_model()
    
    instructions = (
        "Analyze if request needs follow-up. Return JSON only:\n"
        '{ "needs_followup": true/false, "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "true=vague ('build CRM'); false=specific ('landing page for SaaS targeting developers with pricing'). Check: industry, audience, features, purpose."
    )
    prompt = instructions + "\n\nUser request:\n" + json.dumps(user_text)
    
    print(f"[QUERY_DETAIL_ANALYSIS] Using {model_family} model: {model}")
    
    fallback_models = [provider.get_smaller_model(), provider.get_default_model()]
    
    try:
        out = provider.generate_text(prompt, model=model, fallback_models=fallback_models)
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
        return True, 0.0
    except Exception as e:
        print(f"[QUERY_DETAIL_ANALYSIS] Error: {e}")
        return True, 0.0


def chat_response(user_text: str, model_family: str = "gemini", model: str = None) -> str:
    """
    Generate chat response using specified model family.
    
    Args:
        user_text: User input text
        model_family: "gemini", "gpt", or "claude"
        model: Specific model name (optional)
    
    Returns:
        Chat response string
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_smaller_model()
    
    return provider.generate_text(user_text, model=model)


def classify_modification_complexity(instruction: str, model_family: str = "gemini", model: str = None) -> Tuple[str, dict]:
    """
    Classify modification complexity using specified model family.
    
    Args:
        instruction: Modification instruction
        model_family: "gemini", "gpt", or "claude"
        model: Specific model name (optional)
    
    Returns:
        Tuple of (complexity: str, metadata dict)
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_smaller_model()
    
    instructions = (
        "Classify modification complexity. Return JSON only:\n"
        '{ "complexity": "low|medium|high", "explanation": "<1-2 sentence>", "confidence": 0.0 }\n'
        "low=simple (change text/color); medium=moderate (add component/modify layout); high=complex (refactor/major changes)."
    )
    prompt = instructions + "\n\nModification request:\n" + json.dumps(instruction)
    
    print(f"[MODIFICATION_COMPLEXITY] Using {model_family} model: {model}")
    
    fallback_models = [provider.get_smaller_model(), provider.get_default_model()]
    
    try:
        out = provider.generate_text(prompt, model=model, fallback_models=fallback_models)
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
            result = {
                "explanation": explanation,
                "confidence": confidence,
                "raw": out,
                "model": model,
                "model_family": model_family
            }
            print(f"[MODIFICATION_COMPLEXITY] Result: complexity={complexity}, confidence={confidence:.2f}")
            return complexity, result
        result = {
            "explanation": "Could not parse complexity output",
            "confidence": 0.0,
            "raw": out,
            "model": model,
            "model_family": model_family
        }
        return "medium", result
    except Exception as e:
        result = {
            "explanation": f"complexity classifier error: {e}",
            "confidence": 0.0,
            "raw": "",
            "model": model,
            "model_family": model_family
        }
        print(f"[MODIFICATION_COMPLEXITY] Error: {e}")
        return "medium", result


def generate_feature_recommendations(
    page_type_key: str,
    questionnaire_answers: dict,
    page_type_config: dict = None,
    model_family: str = "gemini",
    model: str = None
) -> Tuple[dict, dict]:
    """
    Generate feature recommendations using specified model family.
    
    Args:
        page_type_key: Page type key
        questionnaire_answers: Dictionary of questionnaire answers
        page_type_config: Page type configuration (optional)
        model_family: "gemini", "gpt", or "claude"
        model: Specific model name (optional)
    
    Returns:
        Tuple of (must_have_features dict, competitor_suggestions dict)
    """
    provider = get_provider(model_family)
    if model is None:
        model = provider.get_smaller_model()
    
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
    
    provider = get_provider(model_family)
    print(f"[FEATURE_RECOMMENDATIONS] Using {model_family} model: {model}")
    print(f"[FEATURE_RECOMMENDATIONS] Page type: {page_type_key}")
    
    fallback_models = [provider.get_smaller_model(), provider.get_default_model()]
    
    try:
        out = provider.generate_text(prompt, model=model, fallback_models=fallback_models)
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
        return {"features": [], "explanation": ""}, {"suggestions": [], "explanation": ""}
    except Exception as e:
        print(f"[FEATURE_RECOMMENDATIONS] Error: {e}")
        return {"features": [], "explanation": ""}, {"suggestions": [], "explanation": ""}


# Re-export parse_project_json and save_project_files from gemini_client for backward compatibility
from models.gemini_client import parse_project_json, save_project_files

