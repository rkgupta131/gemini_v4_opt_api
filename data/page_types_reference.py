# data/page_types_reference.py
"""
Reference data for different page types and their expected features/components.
This data guides the AI in generating appropriate features based on the detected page type.
"""

PAGE_TYPES = {
    "crm_dashboard": {
        "name": "Agency CRM",
        "category": "CRM Dashboard",
        "end_user": "Marketing agency owner who runs a 10-person marketing agency. Currently uses Google Sheets, wants to build a custom CRM to track leads exactly how his team works.",
        "core_pages": [
            "Auth Module",
            "Dashboard (with key metrics)",
            "List (Table) & Detail (Individual Record) View",
            "Forms (CRUD)",
            "Log Activity",
            "Reports & Analytics",
            "Settings / Configuration (User Profile)"
        ],
        "components": [
            {
                "name": "Dashboard",
                "description": "Display Data columns like Lead Name, Status etc."
            },
            {
                "name": "Client Table",
                "description": "Data Grid with sort/filter, pagination, and 'Last Interaction' date."
            },
            {
                "name": "Add Lead Button",
                "description": "Action triggers 'Form' to fill fields of the leads."
            },
            {
                "name": "Activity Timeline",
                "description": "Timeline component showing notes and status changes."
            },
            {
                "name": "Stats Widget",
                "description": "Simple cards for 'Total Revenue' and 'Open Deals'."
            }
        ],
        "keywords": ["crm", "leads", "clients", "customers", "sales", "pipeline", "agency", "dashboard"]
    },
    
    "hr_portal": {
        "name": "Employee Onboarding Portal",
        "category": "HR & Employee Portals (HRMS)",
        "end_user": "HR lead at a growing tech startup. He wants to automate the 'first day' experience for new hires to save time. He needs a tool that looks professional and branded, reinforcing the company culture.",
        "core_pages": [
            "Auth Module",
            "Employee Home",
            "Leave Management",
            "Payroll / Documents (Document Vault)",
            "People Directory",
            "Employee Profile (Self View)",
            "Recruitment (Admin Only)"
        ],
        "components": [
            {
                "name": "Progress Tracker",
                "description": "Circular progress bar showing % complete."
            },
            {
                "name": "Task List",
                "description": "Accordion-style tasks (e.g., 'Sign Contract', 'Upload ID') with checkbox state."
            },
            {
                "name": "Document Uploader",
                "description": "Drag-and-drop zone with status indicator (Pending -> Uploaded -> Verified)."
            }
        ],
        "keywords": ["hr", "employee", "onboarding", "recruitment", "hiring", "payroll", "leave", "hrms"]
    },
    
    "inventory_management": {
        "name": "Inventory Management System",
        "category": "Inventory / Business Ops",
        "end_user": "Manages a mid-sized e-commerce warehouse. She needs a no-frills, high-speed tool for her floor staff to update stock levels on their phones. She values speed and data accuracy over design aesthetics.",
        "core_pages": [
            "Auth Module",
            "Dashboard",
            "Inventory List (All Products / Items)",
            "Item Detail (CRUD Item Form)",
            "Orders / Shipments",
            "Audit Log",
            "Export Report",
            "Settings"
        ],
        "components": [
            {
                "name": "Stock Table",
                "description": "High-density row view with 'In Stock', 'Reserved', 'Available' columns."
            },
            {
                "name": "Barcode Scanner",
                "description": "Mobile-responsive camera view utilizing html5-qrcode library."
            },
            {
                "name": "Quick Adjuster",
                "description": "Plus/Minus stepper buttons for rapid stock updates."
            },
            {
                "name": "Alert Badge",
                "description": "Visual indicator on rows where Stock < Reorder Level."
            },
            {
                "name": "Export Action",
                "description": "Button to download current view as CSV."
            }
        ],
        "keywords": ["inventory", "stock", "warehouse", "products", "items", "barcode", "shipment", "orders"]
    },
    
    "ecommerce_fashion": {
        "name": "D2C Fashion Brand App",
        "category": "E-Commerce",
        "end_user": "Founder of a Gen-Z streetwear brand. She cares deeply about aesthetics ('vibes'), mobile performance and scarcity marketing. She wants the site to look like a high-end Shopify Plus store but cost Rs.0/-.",
        "core_pages": [
            "Home (Hero, Featured Collections)",
            "About / Brand Story",
            "Shop All Products (Product Listing Page with Filters)",
            "Product Detail Page (with Images, Description, Variants)",
            "Shopping Cart (Drawer & Page)",
            "Checkout Flow",
            "Order Confirmation / Thank You",
            "Login / Sign Up / Forgot Password",
            "User Account / Dashboard",
            "Search Results",
            "Contact Us",
            "Refund & Return Policy"
        ],
        "components": [
            {
                "name": "Hero Section",
                "description": "Full-width video background with 'Shop New Drop' CTA."
            },
            {
                "name": "Product Cards",
                "description": "Hover effect (swaps image), price display, and 'Quick Add' button."
            },
            {
                "name": "Filter Sidebar",
                "description": "Search (Size, Color, Price) with instant results."
            },
            {
                "name": "Size Guide Modal",
                "description": "Tabbed table (CM/Inches)."
            },
            {
                "name": "Cart Drawer",
                "description": "Slides from right, updates total via optimistic UI."
            },
            {
                "name": "Stock Ticker",
                "description": "'Only 3 left!' red text indicator."
            },
            {
                "name": "Contact Form with Shop Details",
                "description": "Contact form with Name, Email, Message fields. MUST include shop details: business name, address, phone, email, business hours, and social media links."
            }
        ],
        "keywords": ["fashion", "clothing", "apparel", "streetwear", "d2c", "fashion brand", "clothing store", "fashion store"]
    },
    
    "ecommerce": {
        "name": "General E-commerce Store",
        "category": "E-Commerce",
        "end_user": "Business owner selling physical products online (electronics, books, home goods, general merchandise). Needs a professional online store with product catalog, shopping cart, and checkout functionality.",
        "core_pages": [
            "Home (Hero, Featured Products)",
            "Product Catalog / Shop All",
            "Product Category Pages",
            "Product Detail Page (with Images, Description, Variants)",
            "Shopping Cart",
            "Checkout Flow",
            "Order Confirmation / Thank You",
            "User Account / Dashboard",
            "Order History",
            "Search Results",
            "Contact Us",
            "Shipping & Returns Policy"
        ],
        "components": [
            {
                "name": "Product Grid",
                "description": "Responsive grid layout displaying product cards with image, title, price, and 'Add to Cart' button."
            },
            {
                "name": "Product Filters",
                "description": "Filter sidebar with category, price range, brand, and other relevant filters."
            },
            {
                "name": "Shopping Cart",
                "description": "Cart page with item list, quantity controls, subtotal, and checkout button."
            },
            {
                "name": "Product Reviews",
                "description": "Customer reviews section with star ratings and written feedback on product pages."
            },
            {
                "name": "Search Bar",
                "description": "Header search with autocomplete suggestions and search results page."
            },
            {
                "name": "Wishlist",
                "description": "Save products for later functionality with wishlist page."
            }
        ],
        "keywords": ["ecommerce", "online store", "shop", "store", "products", "cart", "checkout", "retail", "merchandise", "selling online"]
    },
    
    "digital_product_store": {
        "name": "Digital Product (Not Physical)",
        "category": "Digital Product Store",
        "end_user": "A digital nomad selling notion templates and e-books. He wants to keep 100% of his profits and needs a secure way to deliver files automatically without technical setup.",
        "core_pages": [
            "Creator Profile",
            "Product Landing Page",
            "Checkout Overlay",
            "My Library / Downloads Hub",
            "Licensing & Usage Rights",
            "Creator Dashboard",
            "Documentation / Knowledge Base",
            "Settings",
            "Privacy Policy",
            "Terms of Service",
            "Contact Us",
            "Refund Policy"
        ],
        "components": [
            {
                "name": "Product Header",
                "description": "Cover image + Pricing card (Sticky on scroll)."
            },
            {
                "name": "File Vault",
                "description": "Secure download list (locked until payment)."
            },
            {
                "name": "Pricing Tier",
                "description": "Radio selection for 'Standard' vs 'Extended' license."
            },
            {
                "name": "Social Proof",
                "description": "'500+ bought this' dynamic counter."
            },
            {
                "name": "FAQ Accordion",
                "description": "Simple Q&A section for refund policies."
            }
        ],
        "keywords": ["digital", "download", "ebook", "template", "course", "pdf", "file", "license"]
    },
    
    "service_marketplace": {
        "name": "Service Marketplace",
        "category": "Marketplace (Multi-User)",
        "end_user": "Building a local platform for finding tutors. He needs a 'Two-Sided' system where he can onboard tutors (Supply) and let students (Demand) book them, taking a commission on the booking fee.",
        "core_pages": [
            "Platform Home",
            "Auth & Onboarding (Split Flows)",
            "Search & Discovery",
            "Universal Inbox / Messaging Center",
            "User Settings",
            "Wallet / Payout Settings",
            "Trust & Safety Center",
            "User Management (Super Admin)",
            "Commission & Fee Manager (Super Admin)",
            "Dispute Resolution Portal (Super Admin)",
            "Content Moderation Queue (Super Admin)"
        ],
        "components": [
            {
                "name": "Map Interface",
                "description": "Split screen (List on left, Map on right) showing provider pins."
            },
            {
                "name": "Search Bar",
                "description": "Input with date picker and 'Service Type' dropdown."
            },
            {
                "name": "Provider Card",
                "description": "Displays Avatar, Hourly Rate, and 'Verified' badge."
            },
            {
                "name": "Review List",
                "description": "List of text reviews with 1-5 star rendering."
            },
            {
                "name": "Booking Calendar",
                "description": "Time-slot picker blocking unavailable hours."
            }
        ],
        "keywords": ["marketplace", "service", "booking", "provider", "tutor", "freelance", "two-sided", "commission"]
    },
    
    "landing_page": {
        "name": "Landing Page / Marketing Page",
        "category": "Marketing / Lead Generation",
        "end_user": "Business owner, marketer, or entrepreneur who wants to capture leads, promote a product/service, or drive conversions with a single focused page.",
        "core_pages": [
            "Landing Page (Single Page with Sections)",
            "Thank You / Success Page"
        ],
        "components": [
            {
                "name": "Hero Section",
                "description": "Eye-catching header with headline, subheadline, and primary CTA button. Often includes hero image or video background."
            },
            {
                "name": "Features Section",
                "description": "Grid or cards displaying 3-6 key features/benefits with icons and descriptions."
            },
            {
                "name": "Social Proof Section",
                "description": "Testimonials, reviews, client logos, or trust badges to build credibility."
            },
            {
                "name": "Call-to-Action (CTA)",
                "description": "Prominent button(s) throughout the page driving user to take action (Sign Up, Get Started, Download, etc.)."
            },
            {
                "name": "Lead Capture Form",
                "description": "Form for collecting email, name, and other contact information. Can be inline or modal popup."
            },
            {
                "name": "Pricing Section (optional)",
                "description": "Pricing tiers or plans with feature comparison if applicable."
            },
            {
                "name": "FAQ Accordion",
                "description": "Frequently asked questions in expandable accordion format."
            },
            {
                "name": "Footer",
                "description": "Contact info, social links, legal links, and additional navigation."
            }
        ],
        "keywords": ["landing", "page", "marketing", "lead", "conversion", "saas", "product launch", "campaign", "promo"]
    },
    
    "student_portfolio": {
        "name": "Student Portfolio Site",
        "category": "Marketing / Personal Brand",
        "end_user": "A Student wants to build a professional identity with zero technical friction. It must be easy for Recruiters to skim the portfolio and download resume.",
        "core_pages": [
            "Home / Landing Hub",
            "About / Brand Story",
            "Projects / Work Showcase",
            "Contact / Inquiry Gateway"
        ],
        "components": [
            {
                "name": "Resume Download",
                "description": "A sticky button that follows the user as they scroll, allowing one-click access to the PDF resume"
            },
            {
                "name": "Skill/Work Page",
                "description": "Highlight 'Major' work/Skill. (Thesis, Final Project, Python, Leadership, Research)"
            },
            {
                "name": "About Page",
                "description": "A timeline component showing High School -> University -> Internships -> Expected Graduation"
            }
        ],
        "keywords": ["portfolio", "student", "resume", "cv", "personal", "profile", "projects", "skills"]
    },
    
    "hyperlocal_delivery": {
        "name": "Hyper-Local Grocery Delivery",
        "category": "On-Demand / Service App",
        "end_user": "Runs a regional grocery chain. He wants to launch a Direct-to-Consumer delivery service to compete with Instacart. He prioritizes a frictionless, ultra-fast ordering experience for repeat customers.",
        "core_pages": [
            "Customer App - Home / Discovery Dashboard",
            "Customer App - Service / Item Details",
            "Customer App - Request Configuration / Cart",
            "Customer App - Checkout / Order Confirmation",
            "Customer App - Active Order Tracking (Live State)",
            "Customer App - Order History / Past Trips",
            "Customer App - User Profile & Settings",
            "Provider App - Provider Home / Status Toggle",
            "Provider App - Incoming Request Card (Pop-up/Screen)",
            "Provider App - Active Job Dashboard (Execution Mode)",
            "Provider App - Earnings Hub",
            "Provider App - Performance & Ratings",
            "Provider App - Onboarding & Documents",
            "Admin Panel - Operations Dashboard (God View)",
            "Admin Panel - Order / Booking Manager",
            "Admin Panel - User Management (CRM)",
            "Admin Panel - Service & Pricing Configuration",
            "Admin Panel - Dispute Resolution Center"
        ],
        "components": [
            {
                "name": "Category Nav",
                "description": "Horizontal scrollable pills (Fruit, Veg, Dairy) for mobile."
            },
            {
                "name": "Quick Add",
                "description": "Button that expands to - 1 + counter on interaction."
            },
            {
                "name": "Order Tracker",
                "description": "Vertical timeline showing 'Received -> Picked -> En Route -> Delivered'"
            },
            {
                "name": "Address Input",
                "description": "Google Places Autocomplete for precise delivery location."
            },
            {
                "name": "Re-Order Carousel",
                "description": "'Buy Again' section based on order history."
            }
        ],
        "keywords": ["delivery", "grocery", "food", "on-demand", "tracking", "local", "order", "instacart"]
    },
    
    "real_estate_listing": {
        "name": "Real Estate Listing App",
        "category": "Data & Directories",
        "end_user": "A real estate agent who wants his own 'Zillow-like' site to capture leads directly without sharing commissions. He prioritizes high-quality photos and capturing user phone numbers.",
        "core_pages": [
            "Home / Search Hub",
            "Results Directory (The 'Feed')",
            "Item Detail Page (The 'Entity')",
            "Provider / Author Profile",
            "Comparison Page",
            "'Add New Listing' Wizard",
            "My Listings Dashboard",
            "Applicant / Lead Manager",
            "Saved Items / Favorites",
            "Activity History",
            "Alerts / Subscription Management",
            "Category & Tag Manager",
            "Moderation Queue",
            "Monetization / Subscription Plans"
        ],
        "components": [
            {
                "name": "Gallery Carousel",
                "description": "Swipeable image slider with '1/20' counter."
            },
            {
                "name": "Mortgage Calculator",
                "description": "Dynamic slider inputs updating monthly cost."
            },
            {
                "name": "Map",
                "description": "'Draw Search' tool on map."
            },
            {
                "name": "Lead Form",
                "description": "'Schedule Tour' sticky footer on mobile."
            },
            {
                "name": "Filters",
                "description": "Range sliders for Price and Sq Ft."
            }
        ],
        "keywords": ["real estate", "property", "listing", "house", "apartment", "zillow", "rent", "buy", "mortgage"]
    },
    
    "ai_tutor_lms": {
        "name": "AI Tutor LMS",
        "category": "Educational Platform (LMS)",
        "end_user": "A corporate trainer or online course creator. She needs a platform that looks like Udemy but allows her to gate content and issue certificates automatically to employees or students.",
        "core_pages": [
            "Course Catalog (The 'Library')",
            "Course Landing Page (The 'Syllabus')",
            "'My Learning' Dashboard",
            "The Lesson Player (The 'Classroom')",
            "Assessment / Quiz Runner",
            "Certificate of Completion",
            "Instructor Dashboard",
            "Course Builder (The 'Curriculum' Wizard)",
            "Student Progress Manager",
            "Q&A / Discussion Board",
            "Skill Taxonomy Manager",
            "Certification Template Designer"
        ],
        "components": [
            {
                "name": "Course Card",
                "description": "Progress bar overlay + 'Resume' button."
            },
            {
                "name": "Video Player",
                "description": "Custom controls + 'Mark Complete' auto-trigger."
            },
            {
                "name": "Quiz Modal",
                "description": "Multiple choice interaction with instant Red/Green feedback."
            },
            {
                "name": "Sidebar Nav",
                "description": "Collapsible curriculum tree."
            },
            {
                "name": "Certificate Gen",
                "description": "Dynamic canvas rendering User Name + Date."
            }
        ],
        "keywords": ["lms", "learning", "course", "education", "training", "udemy", "quiz", "certificate", "lesson"]
    }
}


def get_page_type_by_key(key: str):
    """Get page type configuration by key."""
    return PAGE_TYPES.get(key)


def get_all_page_types():
    """Get all page type keys and names."""
    return {key: value["name"] for key, value in PAGE_TYPES.items()}


def search_page_type_by_keywords(user_input: str):
    """
    Search for the most relevant page type based on user input keywords.
    Returns: (key, page_type_dict, confidence_score)
    """
    user_input_lower = user_input.lower()
    scores = {}
    
    for key, page_type in PAGE_TYPES.items():
        score = 0
        for keyword in page_type["keywords"]:
            if keyword in user_input_lower:
                score += 1
        scores[key] = score
    
    if not scores or max(scores.values()) == 0:
        return None, None, 0.0
    
    best_key = max(scores, key=scores.get)
    confidence = scores[best_key] / len(PAGE_TYPES[best_key]["keywords"])
    
    return best_key, PAGE_TYPES[best_key], confidence

