# Page Type Detection Feature

## Overview
The webpage builder now intelligently detects the type of page you want to build and automatically includes appropriate features and components based on industry best practices.

## How It Works

### 1. **User Input Analysis**
When you describe what you want to build, the AI analyzes your input to detect the page type:
- **Example:** "I want to build a CRM for my marketing agency"
- **Detection:** `crm_dashboard`

### 2. **Automatic Feature Selection**
Based on the detected page type, the system automatically includes:
- **Core Pages**: Essential pages for that type of application
- **Components**: Specific UI components common to that category
- **User Context**: Typical user needs and expectations

### 3. **Supported Page Types**

| Page Type | Category | Example Use Case |
|-----------|----------|------------------|
| `crm_dashboard` | CRM Dashboard | Lead tracking, customer management |
| `hr_portal` | HR & Employee Portals | Employee onboarding, recruitment |
| `inventory_management` | Inventory / Business Ops | Stock management, warehouse operations |
| `ecommerce_fashion` | E-Commerce | Fashion brand, online store |
| `digital_product_store` | Digital Product Store | Ebooks, templates, downloads |
| `service_marketplace` | Marketplace (Multi-User) | Tutors, freelancers, two-sided marketplace |
| `student_portfolio` | Marketing / Personal Brand | Resume, portfolio showcase |
| `hyperlocal_delivery` | On-Demand / Service App | Grocery delivery, food delivery |
| `real_estate_listing` | Data & Directories | Property listings, real estate |
| `ai_tutor_lms` | Educational Platform | Online courses, learning management |

## Usage Flow

### Step 1: Initial Input
```
User: "Build a CRM for tracking leads at my marketing agency"
```

### Step 2: Detection & Preview
The system:
1. Classifies intent as `webpage_build`
2. Detects page type as `crm_dashboard`
3. Shows preview: "✨ Detected page type: **Agency CRM** (CRM Dashboard)"
4. Lists expected features

### Step 3: Wizard Mode
Displays the detected page type with an expandable section showing:
- **Core Pages**: Auth, Dashboard, List View, Forms, etc.
- **Components**: Client Table, Activity Timeline, Stats Widget, etc.

### Step 4: Generation
The AI generates a complete project with:
- All specified core pages
- Fully functional components
- Proper routing and structure
- TypeScript + React + Vite setup

## Example Features by Type

### CRM Dashboard
- **Pages**: Auth, Dashboard, List/Detail View, Forms, Reports
- **Components**: Data Grid, Add Lead Form, Activity Timeline, Stats Cards

### E-Commerce Fashion
- **Pages**: Home, Shop, Product Detail, Cart, Checkout
- **Components**: Hero Section, Product Cards, Filter Sidebar, Cart Drawer

### Student Portfolio
- **Pages**: Home, About, Contact
- **Components**: Resume Download Button, Skill Timeline, Project Showcase

## Technical Implementation

### Files Modified/Created
1. **`data/page_types_reference.py`**: Complete reference data for all page types
2. **`models/gemini_client.py`**: Added `classify_page_type()` function
3. **`app.py`**: Integrated page type detection and feature generation

### Key Functions
- `classify_page_type(user_text)`: AI-based classification
- `get_page_type_by_key(key)`: Retrieve page type configuration
- `search_page_type_by_keywords(user_input)`: Keyword-based fallback

## Customization

### Adding a New Page Type
Edit `data/page_types_reference.py` and add a new entry:

```python
"my_custom_type": {
    "name": "Display Name",
    "category": "Category Name",
    "end_user": "User persona description",
    "core_pages": ["Page 1", "Page 2"],
    "components": [
        {"name": "Component Name", "description": "What it does"}
    ],
    "keywords": ["keyword1", "keyword2"]
}
```

Then update the classifier in `models/gemini_client.py` to include the new type.

## Benefits

1. **Faster Development**: No need to specify every feature manually
2. **Best Practices**: Components follow industry standards
3. **Comprehensive**: Automatically includes essential pages
4. **Intelligent**: Learns from user description
5. **Flexible**: Works with both AI and manual mode

## Fallback Behavior

If the page type cannot be determined:
- Falls back to `generic` type
- User can still use manual wizard inputs
- Basic project structure is still generated

---

**Version:** 1.0  
**Last Updated:** January 6, 2026






