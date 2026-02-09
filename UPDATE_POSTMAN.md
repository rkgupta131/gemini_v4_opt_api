# Postman Collection Update Instructions

The API no longer requires `action` or `session_id` in the payload. Action is inferred from the payload structure, and session_id is auto-generated if not provided.

## Updated Payload Format

### First Request (Generate Project)
```json
{
  "model_family": "gemini",
  "user_input": "I want to build an e-commerce website",
  "project_id": "proj_123"
}
```

### Follow-up Request (After Questions)
```json
{
  "model_family": "gemini",
  "page_type_key": "ecommerce",
  "questionnaire_answers": {
    "target_audience": "young_adults",
    "product_categories": ["electronics", "clothing"]
  },
  "wizard_inputs": {
    "hero_text": "Welcome to our store",
    "theme": "Light"
  }
}
```

### Modify Project
```json
{
  "model_family": "gemini",
  "instruction": "Change the theme to dark mode",
  "base_project_path": "output/project.json"
}
```

### Chat
```json
{
  "model_family": "gemini",
  "user_input": "What is React?"
}
```

## Action Inference Logic

- `instruction` present → `modify_project`
- `user_input` only → `classify_intent` (determines if chat or webpage_build)
- `user_input` + `page_type_key`/`questionnaire_answers`/`wizard_inputs` → `generate_project`
- `page_type_key`/`questionnaire_answers`/`wizard_inputs` only → `generate_project`

## Session ID

- Optional field
- Auto-generated as `session_{timestamp}` if not provided
- Can be provided to maintain session across requests





