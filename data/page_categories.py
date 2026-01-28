# data/page_categories.py
"""
Page type categories for user selection when query is too vague.
"""

PAGE_CATEGORIES = {
    "crm_dashboard": {
        "display_name": "CRM Dashboard",
        "description": "Customer relationship management, lead tracking, sales pipeline",
        "icon": "📊",
        "examples": "Track leads, manage clients, sales reporting"
    },
    "hr_portal": {
        "display_name": "HR & Employee Portals (HRMS)",
        "description": "Employee management, onboarding, recruitment, payroll",
        "icon": "👥",
        "examples": "Employee onboarding, leave management, recruitment"
    },
    "inventory_management": {
        "display_name": "Inventory / Business Ops",
        "description": "Stock management, warehouse operations, order tracking",
        "icon": "📦",
        "examples": "Inventory tracking, stock alerts, order management"
    },
    "ecommerce": {
        "display_name": "E-Commerce",
        "description": "General online store, product catalog, shopping cart, checkout",
        "icon": "🛒",
        "examples": "Online store, product listings, shopping cart"
    },
    "ecommerce_fashion": {
        "display_name": "Fashion E-Commerce",
        "description": "Fashion/clothing store, apparel, accessories, fashion brand",
        "icon": "👗",
        "examples": "Fashion store, clothing brand, apparel shop"
    },
    "digital_product_store": {
        "display_name": "Digital Product Store",
        "description": "Sell digital downloads, templates, ebooks, courses",
        "icon": "💾",
        "examples": "E-books, Notion templates, design assets"
    },
    "service_marketplace": {
        "display_name": "Marketplace (Multi-User)",
        "description": "Two-sided platform, service providers, bookings",
        "icon": "🤝",
        "examples": "Tutors marketplace, freelance platform, service booking"
    },
    "landing_page": {
        "display_name": "Landing Page / Marketing",
        "description": "Single promotional page, lead capture, product launch",
        "icon": "🚀",
        "examples": "Product launch, lead generation, campaign page"
    },
    "student_portfolio": {
        "display_name": "Marketing / Personal Brand",
        "description": "Portfolio, resume showcase, personal website",
        "icon": "💼",
        "examples": "Student portfolio, personal brand, resume site"
    },
    "hyperlocal_delivery": {
        "display_name": "On-Demand / Service App",
        "description": "Food delivery, grocery delivery, on-demand services",
        "icon": "🚚",
        "examples": "Food delivery, grocery app, ride sharing"
    },
    "real_estate_listing": {
        "display_name": "Data & Directories",
        "description": "Listings, directories, property search, classifieds",
        "icon": "🏢",
        "examples": "Real estate listings, job board, directory"
    },
    "ai_tutor_lms": {
        "display_name": "Educational Platform (LMS)",
        "description": "Online courses, learning management, certification",
        "icon": "🎓",
        "examples": "Online courses, training platform, e-learning"
    }
}


def get_all_categories():
    """Get all page categories for display."""
    return PAGE_CATEGORIES


def get_category_display_names():
    """Get list of category display names."""
    return [info["display_name"] for key, info in PAGE_CATEGORIES.items()]


def get_category_key_from_display_name(display_name: str):
    """Get the key from display name."""
    for key, info in PAGE_CATEGORIES.items():
        if info["display_name"] == display_name:
            return key
    return None






