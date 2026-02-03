# Model Family Support Guide

This API now supports multiple model families: **Gemini**, **GPT**, and **Claude**. You can specify which model family to use for all LLM operations.

## Supported Model Families

### 1. Gemini (Default)
- **Provider**: Google Vertex AI
- **Required Environment Variables**: 
  - `GOOGLE_CLOUD_PROJECT`
  - `GOOGLE_CLOUD_LOCATION` (optional, defaults to "global")
- **Models Used**:
  - Intent/Classification: `gemini-2.0-flash-lite`
  - Project Generation: `gemini-3-pro-preview`
  - Chat: `gemini-2.0-flash-lite`

### 2. GPT
- **Provider**: OpenAI
- **Required Environment Variables**: 
  - `OPENAI_API_KEY`
- **Models Used**:
  - Intent/Classification: `gpt-4o-mini`
  - Project Generation: `gpt-4o`
  - Chat: `gpt-4o-mini`

### 3. Claude
- **Provider**: Anthropic
- **Required Environment Variables**: 
  - `ANTHROPIC_API_KEY`
- **Models Used**:
  - Intent/Classification: `claude-3-haiku-20240307`
  - Project Generation: `claude-3-5-sonnet-20241022`
  - Chat: `claude-3-haiku-20240307`

## Usage

### In API Requests

Add `model_family` parameter to your requests:

```json
{
  "action": "classify_intent",
  "session_id": "session_123",
  "model_family": "gpt",
  "user_input": "I want to build an e-commerce website"
}
```

### Supported Values

- `"gemini"` (default)
- `"gpt"`
- `"claude"`

### Example Requests

#### Using Gemini (Default)
```json
{
  "action": "generate_project",
  "session_id": "session_123",
  "model_family": "gemini",
  "page_type_key": "ecommerce",
  "wizard_inputs": {
    "hero_text": "Welcome",
    "subtext": "Best products",
    "cta": "Shop Now",
    "theme": "Light"
  }
}
```

#### Using GPT
```json
{
  "action": "generate_project",
  "session_id": "session_123",
  "model_family": "gpt",
  "page_type_key": "ecommerce",
  "wizard_inputs": {...}
}
```

#### Using Claude
```json
{
  "action": "generate_project",
  "session_id": "session_123",
  "model_family": "claude",
  "page_type_key": "ecommerce",
  "wizard_inputs": {...}
}
```

## Model Selection Logic

The API automatically selects appropriate models based on:

1. **Task Complexity**:
   - **Low/Simple**: Uses smaller, faster models (e.g., `gemini-2.0-flash-lite`, `gpt-4o-mini`, `claude-3-haiku`)
   - **High/Complex**: Uses more capable models (e.g., `gemini-3-pro-preview`, `gpt-4o`, `claude-3-5-sonnet`)

2. **Operation Type**:
   - **Intent Classification**: Smaller model
   - **Page Type Classification**: Smaller model
   - **Project Generation**: Default/larger model
   - **Modifications**: Based on complexity classification

## Environment Setup

### For Gemini
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # Optional
```

### For GPT
```bash
export OPENAI_API_KEY="sk-..."
```

### For Claude
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Installation

Install required packages:

```bash
pip install -r requiremnets.txt
```

This will install:
- `google-genai` (for Gemini)
- `openai` (for GPT)
- `anthropic` (for Claude)

## Error Handling

If a model family is not available (missing API key or package), the API will return an error:

```json
{
  "type": "error",
  "message": "Failed to initialize gpt provider: OPENAI_API_KEY is not set in environment variables"
}
```

## Backward Compatibility

If `model_family` is not specified, the API defaults to `"gemini"` for backward compatibility.

## Architecture

The system uses a provider pattern:

1. **Base Provider** (`models/base_provider.py`): Abstract interface
2. **Family Providers** (`models/providers/`): Implementation for each family
3. **Model Factory** (`models/model_factory.py`): Creates appropriate provider
4. **Unified Client** (`models/unified_client.py`): Single interface for all families

This makes it easy to:
- Add new model families
- Switch between families seamlessly
- Maintain consistent API across families




