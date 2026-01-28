# data/questionnaire_config.py
"""
MCQ questionnaire configurations for different page types.
These questions help gather specific requirements when user input is vague.
"""
import json
from typing import Optional, Dict, Any

# Cache for generated questionnaires (avoids regeneration)
_questionnaire_cache: Dict[str, Dict[str, Any]] = {}

QUESTIONNAIRES = {
    "landing_page": {
        "questions": [
            {
                "id": "industry",
                "question": "What industry/category is this landing page for?",
                "type": "radio",
                "options": [
                    "SaaS / Software Product",
                    "E-commerce / Online Store",
                    "Agency / Services",
                    "Education / Course",
                    "Health & Wellness",
                    "Real Estate",
                    "Finance / Fintech",
                    "Event / Webinar",
                    "Mobile App",
                    "Other"
                ]
            },
            {
                "id": "primary_goal",
                "question": "What's the primary goal of this landing page?",
                "type": "radio",
                "options": [
                    "Lead Generation (Capture emails/contacts)",
                    "Product Launch / Announcement",
                    "Event Registration / Sign-ups",
                    "Free Trial / Demo Request",
                    "Direct Sales / Purchase",
                    "Download (Ebook, App, Resource)",
                    "Newsletter Subscription",
                    "Consultation Booking"
                ]
            },
            {
                "id": "target_audience",
                "question": "Who is your target audience?",
                "type": "radio",
                "options": [
                    "B2B (Businesses)",
                    "B2C (Consumers)",
                    "Developers / Technical",
                    "Students / Educators",
                    "Professionals / Executives",
                    "General Public",
                    "Small Business Owners"
                ]
            },
            {
                "id": "design_style",
                "question": "What design style do you prefer? (applies to layout, colors, typography, and overall visual aesthetic)",
                "type": "radio",
                "options": [
                    "Modern & Minimal (clean lines, white space, sans-serif fonts, muted colors)",
                    "Bold & Colorful (vibrant colors, strong contrasts, eye-catching visuals)",
                    "Professional & Corporate (formal layout, conservative colors, serif fonts, structured)",
                    "Creative & Artistic (unique layouts, artistic elements, creative typography, expressive)",
                    "Tech / Startup Vibe (modern gradients, tech icons, bold CTAs, innovative design)"
                ]
            },
            {
                "id": "features",
                "question": "Which features do you want to include? (Select all that apply - these are must-have features)",
                "type": "multiselect",
                "options": [
                    "Hero Video/Animation (full-width video background in hero section)",
                    "Customer Testimonials (testimonial cards with quotes and photos)",
                    "Pricing Table (pricing tiers with feature comparison)",
                    "FAQ Section (expandable accordion with common questions)",
                    "Product Demo/Screenshots (visual showcase of product features)",
                    "Trust Badges/Logos (partner/client logos, security badges)",
                    "Live Chat Widget (floating chat button for customer support)",
                    "Social Proof Counter (dynamic counters showing users, downloads, etc.)"
                ]
            }
        ]
    },
    
    "crm_dashboard": {
        "questions": [
            {
                "id": "business_type",
                "question": "What type of business is this CRM for?",
                "type": "radio",
                "options": [
                    "Marketing Agency",
                    "Sales Team",
                    "Real Estate",
                    "Consulting Firm",
                    "E-commerce Business",
                    "B2B Services",
                    "Freelancer/Solopreneur"
                ]
            },
            {
                "id": "team_size",
                "question": "How large is your team?",
                "type": "radio",
                "options": [
                    "Solo (Just me)",
                    "Small (2-10 people)",
                    "Medium (11-50 people)",
                    "Large (50+ people)"
                ]
            },
            {
                "id": "key_features",
                "question": "What are your most important CRM features? (Select all that apply - these are must-have features)",
                "type": "multiselect",
                "options": [
                    "Lead Management (capture, track, and manage leads through sales funnel)",
                    "Deal Pipeline Tracking (visual pipeline with stages: New, Qualified, Proposal, Closed)",
                    "Activity Timeline (chronological log of calls, emails, meetings per contact)",
                    "Email Integration (sync emails with contacts, send emails from CRM)",
                    "Task Management (create and assign tasks, set reminders, track completion)",
                    "Reporting & Analytics (dashboards with metrics, charts, revenue reports)",
                    "Contact Segmentation (group contacts by tags, industry, status, custom fields)",
                    "Document Storage (upload and attach files to contacts/deals, file library)"
                ]
            },
            {
                "id": "integration_needs",
                "question": "Do you need integrations? (Select all that apply - these will be integrated or prepared for integration)",
                "type": "multiselect",
                "options": [
                    "Email (Gmail, Outlook) - sync emails, send emails from CRM, email tracking",
                    "Calendar (Google Calendar, Outlook) - sync calendar events, schedule meetings",
                    "Spreadsheets (Google Sheets, Excel) - import/export data, sync with spreadsheets",
                    "Payment Processing (Stripe, PayPal) - process payments, handle transactions",
                    "Marketing Tools (Mailchimp, HubSpot) - sync contacts, marketing automation",
                    "No integrations needed - standalone CRM without external integrations"
                ]
            }
        ]
    },
    
    "ecommerce_fashion": {
        "questions": [
            {
                "id": "store_type",
                "question": "What type of fashion products do you sell?",
                "type": "radio",
                "options": [
                    "Streetwear / Urban Fashion",
                    "Luxury / High-End Fashion",
                    "Casual / Everyday Wear",
                    "Sportswear / Activewear",
                    "Accessories / Jewelry",
                    "Sustainable / Eco Fashion"
                ]
            },
            {
                "id": "target_market",
                "question": "Who is your target market?",
                "type": "radio",
                "options": [
                    "Gen-Z (18-24)",
                    "Millennials (25-40)",
                    "Young Professionals",
                    "Premium/Luxury Buyers",
                    "Budget-Conscious Shoppers"
                ]
            },
            {
                "id": "store_features",
                "question": "Which e-commerce features do you need? (Select all that apply - these are must-have features)",
                "type": "multiselect",
                "options": [
                    "Product Filters (Size, Color, Price) - filter sidebar with instant results",
                    "Wishlist / Favorites - save products for later, wishlist page",
                    "Size Guide - modal/popup with size chart in CM and Inches",
                    "Product Reviews - customer reviews with star ratings on product pages",
                    "Quick View - quick preview modal without leaving listing page",
                    "Stock Availability Alerts - 'Only X left!' indicators, low stock warnings",
                    "Gift Cards - purchase and redeem gift cards functionality",
                    "Referral Program - referral links, rewards for sharing, referral tracking"
                ]
            },
            {
                "id": "visual_aesthetic_vibe",
                "question": "What's the visual aesthetic/vibe? (applies to colors, typography, imagery style, and overall brand personality)",
                "type": "radio",
                "options": [
                    "Edgy & Bold (dark colors, bold typography, streetwear aesthetic, high contrast)",
                    "Minimalist & Clean (neutral colors, simple layouts, clean typography, spacious)",
                    "Luxury & Elegant (premium colors like gold/black, sophisticated fonts, high-end imagery)",
                    "Fun & Playful (bright colors, playful fonts, casual imagery, energetic vibe)",
                    "Earthy & Natural (warm earth tones, organic shapes, natural textures, sustainable feel)"
                ]
            }
        ]
    },
    
    "ecommerce": {
        "questions": [
            {
                "id": "product_category",
                "question": "What type of products are you selling?",
                "type": "radio",
                "options": [
                    "Electronics / Tech",
                    "Books / Media",
                    "Home & Garden",
                    "Health & Beauty",
                    "Sports & Outdoors",
                    "Toys & Games",
                    "Automotive",
                    "Food & Beverages",
                    "Other"
                ]
            },
            {
                "id": "target_audience",
                "question": "Who is your target audience?",
                "type": "radio",
                "options": [
                    "B2C (Individual Consumers)",
                    "B2B (Businesses)",
                    "General Public",
                    "Niche Market",
                    "Price-Conscious Shoppers",
                    "Premium Buyers"
                ]
            },
            {
                "id": "store_features",
                "question": "Which e-commerce features do you need? (Select all that apply - these are must-have features)",
                "type": "multiselect",
                "options": [
                    "Product Filters (Category, Price, Brand) - filter sidebar with instant results",
                    "Product Reviews & Ratings - customer reviews with star ratings on product pages",
                    "Wishlist / Favorites - save products for later, wishlist page",
                    "Search Functionality - search bar with autocomplete and search results",
                    "Shopping Cart - cart page with quantity controls and checkout",
                    "User Accounts - customer accounts with order history",
                    "Product Recommendations - 'You may also like' or 'Related products'",
                    "Multiple Payment Options - credit card, PayPal, etc."
                ]
            },
            {
                "id": "shipping_needs",
                "question": "What shipping options do you need?",
                "type": "multiselect",
                "options": [
                    "Standard Shipping",
                    "Express Shipping",
                    "Free Shipping Threshold",
                    "International Shipping",
                    "Local Pickup",
                    "Shipping Calculator"
                ]
            }
        ]
    },
    
    "student_portfolio": {
        "questions": [
            {
                "id": "field",
                "question": "What field are you studying/working in?",
                "type": "radio",
                "options": [
                    "Computer Science / Engineering",
                    "Design / UX/UI",
                    "Business / Marketing",
                    "Data Science / Analytics",
                    "Creative Arts / Media",
                    "Research / Academia",
                    "Other"
                ]
            },
            {
                "id": "career_stage",
                "question": "What stage are you at?",
                "type": "radio",
                "options": [
                    "Current Student",
                    "Recent Graduate",
                    "Looking for Internship",
                    "Looking for Full-Time Job",
                    "Career Switch"
                ]
            },
            {
                "id": "showcase_items",
                "question": "What do you want to showcase? (Select all that apply - these will be featured sections)",
                "type": "multiselect",
                "options": [
                    "Academic Projects (university projects, thesis, coursework with descriptions and links)",
                    "Work Experience (job history, internships, roles with descriptions and dates)",
                    "Technical Skills (programming languages, tools, technologies with proficiency levels)",
                    "Certifications (certificates, courses, credentials with issue dates and organizations)",
                    "Research Papers (published papers, research work with links and abstracts)",
                    "Side Projects (personal projects, hobby projects with descriptions and demos)",
                    "Open Source Contributions (GitHub contributions, open source projects, pull requests)",
                    "Awards & Achievements (awards, honors, competitions, recognitions with dates)"
                ]
            }
        ]
    },
    
    "service_marketplace": {
        "questions": [
            {
                "id": "service_category",
                "question": "What type of services will be offered?",
                "type": "radio",
                "options": [
                    "Education / Tutoring",
                    "Home Services (Cleaning, Repairs)",
                    "Professional Services (Legal, Accounting)",
                    "Creative Services (Design, Writing)",
                    "Health & Wellness",
                    "Event Services",
                    "Transportation / Delivery"
                ]
            },
            {
                "id": "booking_type",
                "question": "How should booking work?",
                "type": "radio",
                "options": [
                    "Instant Booking (Immediate confirmation)",
                    "Request to Book (Provider approves)",
                    "Quote-Based (Provider sends estimate)",
                    "Scheduling Only (No payment)"
                ]
            },
            {
                "id": "marketplace_features",
                "question": "Which marketplace features do you need? (Select all that apply - these are must-have features)",
                "type": "multiselect",
                "options": [
                    "Provider Profiles & Verification (detailed provider pages, verification badges, credentials)",
                    "Reviews & Ratings (5-star rating system, text reviews, review moderation)",
                    "In-App Messaging (real-time chat between providers and customers)",
                    "Payment Processing (secure payment gateway, transaction handling, refunds)",
                    "Calendar/Availability (provider calendar, time slot booking, availability management)",
                    "Location/Map Search (map-based search, location filters, distance calculation)",
                    "Dispute Resolution (dispute filing, admin mediation, resolution tracking)",
                    "Commission Management (automatic commission calculation, payout tracking, fee settings)"
                ]
            }
        ]
    },
    
    "digital_product_store": {
        "questions": [
            {
                "id": "product_type",
                "question": "What type of digital products are you selling?",
                "type": "radio",
                "options": [
                    "E-books / Guides",
                    "Notion Templates",
                    "Design Assets (Fonts, Icons, Templates)",
                    "Online Courses / Video Content",
                    "Software / Tools",
                    "Music / Audio",
                    "Photos / Stock Images"
                ]
            },
            {
                "id": "pricing_model",
                "question": "What's your pricing model?",
                "type": "radio",
                "options": [
                    "One-Time Purchase",
                    "Tiered Pricing (Standard/Extended License)",
                    "Subscription (Monthly/Annual)",
                    "Freemium (Free + Paid)",
                    "Pay What You Want"
                ]
            },
            {
                "id": "delivery_features",
                "question": "Which features do you need? (Select all that apply - these are must-have features)",
                "type": "multiselect",
                "options": [
                    "Secure File Delivery (automatic download links after purchase, secure file hosting)",
                    "License Management (track license types, usage rights, license keys generation)",
                    "Automatic Updates (notify customers of updates, version tracking, update downloads)",
                    "Customer Library/Dashboard (personal dashboard showing purchased products, download history)",
                    "Preview/Demo Access (free preview of products before purchase, demo versions)",
                    "Affiliate Program (affiliate links, commission tracking, referral system)",
                    "Bundle Discounts (discount packages, bundle pricing, cross-sell bundles)"
                ]
            }
        ]
    },
    
    "generic": {
        "questions": [
            {
                "id": "purpose",
                "question": "What's the main purpose of your website?",
                "type": "radio",
                "options": [
                    "Business/Marketing",
                    "Personal Blog",
                    "Portfolio",
                    "Information/Documentation",
                    "Community/Forum",
                    "Other"
                ]
            },
            {
                "id": "key_pages",
                "question": "Which pages do you need?",
                "type": "multiselect",
                "options": [
                    "Home Page",
                    "About Page",
                    "Contact Page",
                    "Services/Products Page",
                    "Blog",
                    "Gallery",
                    "Testimonials"
                ]
            }
        ]
    }
}


def generate_questionnaire_llm(page_type_key: str) -> Optional[Dict[str, Any]]:
    """
    Generate questionnaire using LLM with minimal token usage.
    Uses hardcoded as compact reference template.
    """
    try:
        from models.gemini_client import generate_text, get_smaller_model
        
        # Get hardcoded reference
        ref = QUESTIONNAIRES.get(page_type_key, QUESTIONNAIRES.get("generic"))
        if not ref:
            return None
        
        # Compact JSON (minimal tokens - no spaces)
        ref_json = json.dumps(ref, separators=(',', ':'))
        
        # Ultra-minimal prompt (optimized for token usage)
        prompt = f"Q:{page_type_key}\nR:{ref_json}\nReturn same structure as R."
        
        model = get_smaller_model()
        out = generate_text(prompt, model=model)
        
        # Parse JSON
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1:
            parsed = json.loads(out[start:end+1])
            # Validate structure
            if "questions" in parsed and isinstance(parsed["questions"], list):
                return parsed
    except Exception as e:
        print(f"[QUESTIONNAIRE_LLM] Failed: {e}")
    
    return None

def get_questionnaire(page_type_key: str, use_llm: bool = True) -> Dict[str, Any]:
    """
    Get questionnaire - uses LLM (cached) or falls back to hardcoded.
    Optimized for minimal token usage with caching.
    """
    # Check cache first (avoids regeneration - zero tokens)
    cache_key = f"{page_type_key}_llm" if use_llm else f"{page_type_key}_ref"
    if cache_key in _questionnaire_cache:
        return _questionnaire_cache[cache_key]
    
    # Try LLM generation if enabled
    if use_llm:
        llm_result = generate_questionnaire_llm(page_type_key)
        if llm_result:
            _questionnaire_cache[cache_key] = llm_result
            return llm_result
    
    # Fallback to hardcoded reference
    result = QUESTIONNAIRES.get(page_type_key, QUESTIONNAIRES.get("generic"))
    _questionnaire_cache[cache_key] = result
    return result

def has_questionnaire(page_type_key: str) -> bool:
    """Check if a page type has a questionnaire."""
    return page_type_key in QUESTIONNAIRES






