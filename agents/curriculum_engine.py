"""Curriculum Engine: Master Syllabus & Topic Registry for Digital Marketing & Server-Side Tracking.

Root Instruction source: Complete Digital Marketing with Web Analytics and Server Side Tracking
Syllabus Modules (25 Classes + Paid Ads + Analytics + Freelancing):
- Class 1-3: Web Analytics & Google Tag Manager DataLayer Concepts (WordPress/WooCommerce)
- Class 4-6: Facebook Pixel Web Events Tracking (Dynamic Values, Custom Events)
- Class 7-9: Facebook Conversion API (CAPI) Setup (Stape.io, First-Party Cookies, iOS 14.5, Deduplication)
- Class 10-13: GA4 Browser & Server-Side E-Commerce Tracking
- Class 14: Google Ads Conversion Tracking & Dynamic Remarketing
- Class 15: Various Form Tracking Techniques (CF7, Calendly, Element Visibility)
- Class 16-18: Shopify CMS DataLayer & Server-Side Facebook CAPI
- Class 19: Custom JavaScript for Marketers (DOM Scraping, LocalStorage, Match Quality)
- Class 20-21: Snap Pixel & TikTok Pixel Conversion API with GTM
- Class 22: Fiverr Marketplace & Gig Creation
- Class 23: Installing GTM & DataLayer on CMS (Squarespace, Wix, ClickFunnels, GHL)
- Class 24: Facebook Pixel Setup via JavaScript with Dynamic Values
- Class 25: Cookie Consent Banner V2 (GDPR/CCPA, Google Consent Mode V2)
- Paid Advertising: Meta Andromeda 2026, Google Smart Bidding, TikTok Ads, ChatGPT Ads
- Client Hunting & High-Ticket Outbound Acquisition
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from state import ResearchTopic


class CurriculumTopic(BaseModel):
    """Structured syllabus lesson mapped to actionable daily tips and tricks."""
    class_id: int = Field(..., description="Class or module number from syllabus")
    module_category: str = Field(..., description="Core syllabus category")
    title: str = Field(..., description="High-converting topic headline")
    problem_statement: str = Field(..., description="Real-world bottleneck or data loss pain point")
    actionable_tip: str = Field(..., description="Exact tip/trick for resolution")
    code_snippet: str = Field(..., description="Working JavaScript, GTM DataLayer, or CAPI payload")
    roi_metric_label: str = Field(default="Data Accuracy")
    roi_metric_value: str = Field(default="+38%")
    roi_subtext: str = Field(default="Recovered post-iOS 14.5")
    checklist_items: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


# The Master 25-Class + Advanced Modules Curriculum Bank
CURRICULUM_BANK: List[CurriculumTopic] = [
    # Day 1: Class 1-3 (Web Analytics & GTM DataLayer Fundamentals)
    CurriculumTopic(
        class_id=1,
        module_category="Web Analytics & GTM DataLayer Fundamentals",
        title="Web Analytics & GTM DataLayer: The Single Source of Truth Architecture",
        problem_statement="Relying on direct DOM element scraping or fragile CSS click triggers breaks analytics tracking every time a web developer updates website styling or layouts.",
        actionable_tip="Establish a structured, vendor-neutral DataLayer push architecture (window.dataLayer.push) on WordPress/WooCommerce that cleanly separates frontend design from marketing tags.",
        code_snippet=(
            "// Standard GTM DataLayer Push Architecture\n"
            "window.dataLayer = window.dataLayer || [];\n"
            "window.dataLayer.push({\n"
            "  event: 'custom_conversion_signal',\n"
            "  user_status: 'vip_prospect',\n"
            "  cart_total: 249.00,\n"
            "  currency: 'USD'\n"
            "});"
        ),
        roi_metric_label="Tracking Reliability",
        roi_metric_value="99.9%",
        roi_subtext="Zero broken tags post-UI updates",
        checklist_items=[
            "Install GTM container snippet in <head> and immediately after <body>",
            "Initialize window.dataLayer above GTM snippet",
            "Map DataLayer Variables in GTM using Version 2 schema",
            "Validate event payloads in GTM Preview & Debug Console"
        ],
        tags=["#WebAnalytics", "#GoogleTagManager", "#DataLayer", "#ConversionTracking", "#TipuSultan"]
    ),
    # Day 2: Class 4-6 (Facebook Pixel Web Events Tracking)
    CurriculumTopic(
        class_id=4,
        module_category="Facebook Pixel Web Events Tracking",
        title="Facebook Pixel Dynamic Values & Custom Events: Unlocking Value-Based Bidding",
        problem_statement="Firing generic PageView or standard events without dynamic value and currency parameters forces Meta AI to optimize for cheap clicks instead of high-paying buyers.",
        actionable_tip="Inject dynamic value, currency, content_name, and content_type parameters using GTM DataLayer variables directly into fbq('track', 'AddToCart') and fbq('track', 'Purchase').",
        code_snippet=(
            "// Dynamic Meta Pixel Standard Event with Value\n"
            "fbq('track', 'AddToCart', {\n"
            "  content_name: {{dlv - product_name}},\n"
            "  content_ids: [{{dlv - product_id}}],\n"
            "  content_type: 'product',\n"
            "  value: {{dlv - product_price}},\n"
            "  currency: 'USD'\n"
            "});"
        ),
        roi_metric_label="ROAS Improvement",
        roi_metric_value="+34%",
        roi_subtext="Via Meta Value-Based Optimization (VBO)",
        checklist_items=[
            "Configure Base Pixel in GTM All Pages trigger",
            "Map dynamic product variables from DataLayer",
            "Trigger standard eCommerce events (ViewContent, AddToCart, InitiateCheckout)",
            "Audit event parameters inside Meta Pixel Helper extension"
        ],
        tags=["#MetaPixel", "#FacebookAds", "#DynamicValues", "#GoogleTagManager", "#GrowthArchitect"]
    ),
    # Day 3: Class 7 (Stape.io CAPI Setup & First-Party Cookies)
    CurriculumTopic(
        class_id=7,
        module_category="Server-Side Tracking & CAPI",
        title="Fixing iOS 14.5 & AdBlocker Data Loss with Stape.io & First-Party Cookies",
        problem_statement="Standard browser Meta Pixel loses 30-45% of purchase events due to Safari ITP, iOS privacy controls, and client-side ad blockers.",
        actionable_tip="Route events through a GTM Server Container hosted on Stape.io using a custom domain (e.g. data.yourdomain.com) to restore 1st-party cookie lifespan from 24 hours back to 365 days.",
        code_snippet=(
            "// Server-Side First-Party Cookie Setter via GTM\n"
            "function setFirstPartyFbp() {\n"
            "  var fbp = getCookie('_fbp');\n"
            "  if (!fbp) {\n"
            "    fbp = 'fb.1.' + Date.now() + '.' + Math.floor(Math.random() * 1000000000);\n"
            "  }\n"
            "  setCookie('_fbp', fbp, 365, 'yourdomain.com'); // First-party context\n"
            "  return fbp;\n"
            "}"
        ),
        roi_metric_label="Event Match Quality",
        roi_metric_value="9.4 / 10",
        roi_subtext="From standard 4.8 baseline",
        checklist_items=[
            "Deploy custom sub-domain DNS record (CNAME to Stape.io)",
            "Enable First-Party Cookie lifespan extension",
            "Generate server-side fbp & fbc parameters",
            "Verify real-time incoming requests in GTM Server Preview"
        ],
        tags=["#ServerSideTracking", "#MetaCAPI", "#GTM", "#StapeIO", "#DataDrivenGrowth"]
    ),
    # Day 4: Class 8 (Event Deduplication: event_id)
    CurriculumTopic(
        class_id=8,
        module_category="Server-Side Tracking & CAPI",
        title="Eliminating Duplicate Conversions: Bulletproof Event Deduplication (event_id)",
        problem_statement="Running both Browser Pixel and Server CAPI simultaneously causes duplicate purchase reporting in Meta Ads Manager if deduplication keys mismatch.",
        actionable_tip="Generate a unique, shared event_id in GTM Web container and pass the exact same string to both browser Pixel and server CAPI payloads so Meta automatically merges them.",
        code_snippet=(
            "// GTM Custom JavaScript Variable: {{Unique Event ID}}\n"
            "function() {\n"
            "  var orderId = {{dlv - purchase.order_id}} || '';\n"
            "  if (orderId) return 'order_' + orderId;\n"
            "  return 'event_' + Date.now() + '_' + Math.floor(Math.random() * 900000 + 100000);\n"
            "}"
        ),
        roi_metric_label="Deduplication Rate",
        roi_metric_value="100%",
        roi_subtext="Zero duplicate conversion inflation",
        checklist_items=[
            "Create Custom JS variable for unique event_id",
            "Map event_id to browser fbq('track', 'Purchase', ..., {eventID})",
            "Forward event_id inside GA4 client to Server Container",
            "Confirm 'Deduplicated' badge inside Meta Events Manager"
        ],
        tags=["#EventDeduplication", "#MetaPixel", "#ConversionAPI", "#WebAnalytics", "#GTM"]
    ),
    # Day 5: Class 10-11 (GA4 E-Commerce Configuration)
    CurriculumTopic(
        class_id=11,
        module_category="GA4 E-Commerce Configuration",
        title="GA4 E-Commerce Tracking: Dynamic Value, Currency & Item Arrays Architecture",
        problem_statement="Improperly formatted item arrays in GA4 purchase events lead to empty revenue reports, incorrect Monetization metrics, and broken ROAS figures.",
        actionable_tip="Enforce strict GA4 recommended eCommerce schema with dynamic value, transaction_id, and standardized items array containing item_id, item_name, and price.",
        code_snippet=(
            "// Standard GA4 Purchase DataLayer Push\n"
            "window.dataLayer = window.dataLayer || [];\n"
            "window.dataLayer.push({\n"
            "  event: 'purchase',\n"
            "  ecommerce: {\n"
            "    transaction_id: 'ORD_2026_9482',\n"
            "    value: 149.99,\n"
            "    tax: 7.50,\n"
            "    shipping: 10.00,\n"
            "    currency: 'USD',\n"
            "    items: [{\n"
            "      item_id: 'SKU_GROWTH_AI',\n"
            "      item_name: 'AI Growth Architecture Bundle',\n"
            "      price: 149.99,\n"
            "      quantity: 1\n"
            "    }]\n"
            "  }\n"
            "});"
        ),
        roi_metric_label="Reporting Discrepancy",
        roi_metric_value="< 1.5%",
        roi_subtext="Between Backend CRM & GA4 revenue",
        checklist_items=[
            "Validate event name matches exact GA4 specification: 'purchase'",
            "Include transaction_id, value, and currency at root ecommerce level",
            "Map DataLayer variables in GTM with version 2 Data Layer Variable",
            "Test live attribution in GA4 DebugView before publishing"
        ],
        tags=["#GA4", "#ECommerceAnalytics", "#GoogleTagManager", "#ConversionTracking", "#DataEngineering"]
    ),
    # Day 6: Class 12-13 (Server-Side GA4 via Server GTM)
    CurriculumTopic(
        class_id=12,
        module_category="Server-Side GA4 & Cloud Architecture",
        title="Server-Side GA4 via Server GTM: Bypassing AdBlockers & Reducing Web Latency",
        problem_statement="Loading heavyweight client-side analytics scripts bloats Core Web Vitals, increases page load time by 1.8s, and loses 25% of visits to content blockers.",
        actionable_tip="Proxy GA4 requests through your Server GTM container. Client sends 1 request to your endpoint; the server dispatches to GA4, Meta, and Google Ads concurrently.",
        code_snippet=(
            "// GTM Server-Side Transformation Rule (Header Cloaking)\n"
            "// In sGTM Client: Normalize client IP & scrub sensitive PII\n"
            "const eventModel = getEventData();\n"
            "if (eventModel.client_id) {\n"
            "  setResponseHeader('X-Server-Processed', 'true');\n"
            "  setCookie('sgtm_session', eventModel.client_id, 365);\n"
            "}"
        ),
        roi_metric_label="Page Speed Boost",
        roi_metric_value="+40%",
        roi_subtext="Reduced client-side JavaScript execution",
        checklist_items=[
            "Create GA4 Client in GTM Server Container",
            "Set Transport URL in Web GA4 tag to custom server subdomain",
            "Configure GA4 Tag in Server Container with Google Analytics 4",
            "Verify real-time event forwarding in sGTM Debugger"
        ],
        tags=["#ServerSideGA4", "#sGTM", "#CoreWebVitals", "#CloudTracking", "#TipuSultan"]
    ),
    # Day 7: Class 14 (Google Ads Enhanced Conversions)
    CurriculumTopic(
        class_id=14,
        module_category="Google Ads Conversion Tracking",
        title="Google Ads Enhanced Conversions via GTM: Unlocking Smart Bidding Accuracy",
        problem_statement="Browser cookie restrictions and cross-device journeys break Google Ads conversion credit, causing Smart Bidding to underbid on high-value prospects.",
        actionable_tip="Pass first-party user data (SHA-256 hashed email, phone, address) with Google Ads Conversion tags in GTM to enable Enhanced Conversions matching.",
        code_snippet=(
            "// GTM User-Provided Data Variable Structure\n"
            "function getUserData() {\n"
            "  return {\n"
            "    email: {{Normalized Email Variable}},\n"
            "    phone_number: {{Normalized Phone Variable}},\n"
            "    address: {\n"
            "      first_name: {{Billing First Name}},\n"
            "      last_name: {{Billing Last Name}},\n"
            "      country: 'SA'\n"
            "    }\n"
            "  };\n"
            "}"
        ),
        roi_metric_label="Smart Bidding ROAS",
        roi_metric_value="+23%",
        roi_subtext="Improved signal feeding Google AI bidder",
        checklist_items=[
            "Turn on Enhanced Conversions in Google Ads Conversion Settings",
            "Create 'User-Provided Data' variable in GTM Web container",
            "Link user-provided data variable to Google Ads Conversion tag",
            "Verify 'Active (Recorded)' status in Google Ads diagnosis tab"
        ],
        tags=["#GoogleAds", "#EnhancedConversions", "#SmartBidding", "#PMax", "#AnalyticsPro"]
    ),
    # Day 8: Class 15 (Lead Form Tracking)
    CurriculumTopic(
        class_id=15,
        module_category="Lead Form & Interaction Tracking",
        title="Lead Form Tracking: CF7, Calendly iFrames & Element Visibility Triggers",
        problem_statement="Standard form submission triggers fail on AJAX forms, embedded Calendly iFrames, and multi-step popups, resulting in zero reported B2B leads.",
        actionable_tip="Deploy DOM event listeners for Contact Form 7 ('wpcf7mailsent'), window message listeners for Calendly, and Element Visibility triggers for thank-you states.",
        code_snippet=(
            "// Calendly iFrame PostMessage Listener in GTM\n"
            "window.addEventListener('message', function(e) {\n"
            "  if (e.data.event && e.data.event.indexOf('calendly') === 0) {\n"
            "    window.dataLayer.push({\n"
            "      event: 'calendly_' + e.data.event.split('.')[1],\n"
            "      calendly_payload: e.data.payload\n"
            "    });\n"
            "  }\n"
            "});"
        ),
        roi_metric_label="B2B Lead Attribution",
        roi_metric_value="100%",
        roi_subtext="Capturing previously lost iFrame bookings",
        checklist_items=[
            "Inject Calendly postMessage listener tag on pages with booking iFrame",
            "Create Custom Event trigger for 'calendly_event_scheduled'",
            "Map CF7 DOM event listener 'wpcf7mailsent'",
            "Dispatch Lead conversions to Meta, Google Ads, and LinkedIn"
        ],
        tags=["#LeadGeneration", "#CalendlyTracking", "#FormTracking", "#B2BGrowth", "#GTM"]
    ),
    # Day 9: Class 16-18 (Shopify CMS Tracking)
    CurriculumTopic(
        class_id=16,
        module_category="Shopify CMS Tracking",
        title="Shopify Checkout Extensibility & Web Pixels API: The Post-Checkout.liquid Tracking Fix",
        problem_statement="Shopify's deprecation of checkout.liquid broke legacy GTM scripts. Stores without Checkout Extensibility fail to fire Purchase events reliably.",
        actionable_tip="Implement Shopify Custom Web Pixels using the analytics.subscribe API to forward checkout and purchase events securely into GTM and Server CAPI.",
        code_snippet=(
            "// Shopify Custom Web Pixel (Checkout Extensibility)\n"
            "analytics.subscribe('checkout_completed', function(event) {\n"
            "  var checkout = event.data.checkout;\n"
            "  window.dataLayer.push({\n"
            "    event: 'shopify_purchase',\n"
            "    transaction_id: checkout.order.id,\n"
            "    value: checkout.totalPrice.amount,\n"
            "    currency: checkout.totalPrice.currencyCode,\n"
            "    email: checkout.email\n"
            "  });\n"
            "});"
        ),
        roi_metric_label="Checkout Accuracy",
        roi_metric_value="99.8%",
        roi_subtext="Zero missed orders post-checkout update",
        checklist_items=[
            "Navigate to Shopify Admin -> Settings -> Customer Events",
            "Create Custom Pixel with sandboxed analytics.subscribe listener",
            "Route custom event payload to GTM Web or Stape Shopify App",
            "Verify test orders in Shopify Admin and Meta Events Manager"
        ],
        tags=["#Shopify", "#ShopifyTracking", "#WebPixelsAPI", "#MetaCAPI", "#ConversionOptimization"]
    ),
    # Day 10: Class 19 (Custom JavaScript for Marketers)
    CurriculumTopic(
        class_id=19,
        module_category="Custom JavaScript for Marketers",
        title="Scraping Dynamic Form Values Without DataLayer for Maximum Match Quality",
        problem_statement="Many custom CMS platforms and legacy landing pages do not provide an eCommerce DataLayer, leaving user email and phone parameters empty.",
        actionable_tip="Use Custom JavaScript DOM selectors and regex normalization to capture email and phone from input fields or URL parameters for SHA-256 advanced matching.",
        code_snippet=(
            "// Custom JS Variable: {{Normalized User Email}}\n"
            "function() {\n"
            "  var emailInput = document.querySelector('input[type=\"email\"], #user_email, input[name=\"email\"]');\n"
            "  if (emailInput && emailInput.value) {\n"
            "    return emailInput.value.trim().toLowerCase();\n"
            "  }\n"
            "  return window.sessionStorage.getItem('lead_email') || '';\n"
            "}"
        ),
        roi_metric_label="Advanced Match Score",
        roi_metric_value="+42%",
        roi_subtext="Attributed directly to Meta & Google Ads",
        checklist_items=[
            "Test DOM querySelector in Chrome DevTools Console",
            "Normalize strings (lowercase, trim whitespace, remove phone dashes)",
            "Hash with SHA-256 before client dispatch or let Server GTM hash",
            "Store in LocalStorage/SessionStorage for multi-step funnels"
        ],
        tags=["#CustomJavaScript", "#GTM", "#DataLayer", "#AdvancedMatching", "#GrowthEngineering"]
    ),
    # Day 11: Class 20-21 (TikTok Pixel & Conversion API)
    CurriculumTopic(
        class_id=20,
        module_category="TikTok Pixel & Conversion API",
        title="TikTok Events API & Pixel Deduplication: Scaling E-Commerce Video Ads",
        problem_statement="TikTok browser pixel loses substantial conversion data on iOS devices, causing high reported Cost Per Complete Payment and erratic campaign scaling.",
        actionable_tip="Implement TikTok Events API via GTM Server Container alongside browser pixel, passing ttclid and event_id for full server-side attribution.",
        code_snippet=(
            "// TikTok Events API Server-Side Payload\n"
            "{\n"
            "  \"event\": \"CompletePayment\",\n"
            "  \"event_id\": \"order_2026_8492\",\n"
            "  \"user\": {\n"
            "    \"ttclid\": {{Cookie - ttclid}},\n"
            "    \"email\": {{sha256_email}},\n"
            "    \"phone\": {{sha256_phone}}\n"
            "  },\n"
            "  \"properties\": {\n"
            "    \"value\": 89.00,\n"
            "    \"currency\": \"USD\"\n"
            "  }\n"
            "}"
        ),
        roi_metric_label="Reported Purchases",
        roi_metric_value="+29%",
        roi_subtext="Attributed post-Events API rollout",
        checklist_items=[
            "Generate TikTok Access Token in Events Manager",
            "Configure TikTok Events API tag in GTM Server Container",
            "Ensure event_id matches browser ttq.track('CompletePayment')",
            "Validate event match status in TikTok Events Manager"
        ],
        tags=["#TikTokAds", "#TikTokCAPI", "#EventsAPI", "#SocialCommerce", "#TipuSultan"]
    ),
    # Day 12: Class 23 (Installing GTM & DataLayer on Diverse CMS)
    CurriculumTopic(
        class_id=23,
        module_category="CMS Integration & Tracking Architecture",
        title="Enterprise GTM & DataLayer Deployment across Wix, Squarespace, & GoHighLevel",
        problem_statement="No-code website builders often sandbox external scripts, stripping DataLayer variables and preventing custom event tracking from firing.",
        actionable_tip="Utilize custom header injection with lightweight iframe bridge scripts or native webhook forwarders to reliably pass eCommerce events from CMS to GTM.",
        code_snippet=(
            "// Lightweight GHL / Funnel Form Webhook Bridge\n"
            "window.addEventListener('message', function(event) {\n"
            "  if (event.data && event.data.type === 'ghl_form_submission') {\n"
            "    window.dataLayer = window.dataLayer || [];\n"
            "    window.dataLayer.push({\n"
            "      event: 'lead_form_submitted',\n"
            "      form_name: event.data.form_name,\n"
            "      lead_email: event.data.contact.email\n"
            "    });\n"
            "  }\n"
            "});"
        ),
        roi_metric_label="Integration Speed",
        roi_metric_value="< 15 Mins",
        roi_subtext="Universal CMS deployment template",
        checklist_items=[
            "Inject GTM container into CMS Custom Code / Header settings",
            "Verify iframe messaging protocols for hosted forms",
            "Test live form submissions in GTM Preview mode",
            "Forward verified lead signals to CAPI & CRM endpoints"
        ],
        tags=["#GoHighLevel", "#Wix", "#Squarespace", "#GTMSetup", "#GrowthHacking"]
    ),
    # Day 13: Class 24 (Facebook Pixel via Pure JavaScript)
    CurriculumTopic(
        class_id=24,
        module_category="Custom JavaScript Pixel Architecture",
        title="Direct JavaScript Facebook Pixel Architecture: Zero-Plugin Hardened Tracking",
        problem_statement="Third-party WordPress tracking plugins frequently conflict, inject database bloat, or fail silently during core CMS updates.",
        actionable_tip="Deploy pure, native JavaScript snippets for Meta Pixel and CAPI that run independently of bloated third-party plugins with dynamic value extraction.",
        code_snippet=(
            "// Pure JavaScript Dynamic Meta Purchase Tracker\n"
            "!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?\n"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};\n"
            "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';\n"
            "n.queue=[];t=b.createElement(e);t.async=!0;\n"
            "t.src=v;s=b.getElementsByTagName(e)[0];\n"
            "s.parentNode.insertBefore(t,s)}(window, document,'script',\n"
            "'https://connect.facebook.net/en_US/fbevents.js');\n"
            "fbq('init', '{{PIXEL_ID}}');\n"
            "fbq('track', 'PageView');"
        ),
        roi_metric_label="Script Execution",
        roi_metric_value="0ms Lag",
        roi_subtext="Zero plugin overhead on server CPU",
        checklist_items=[
            "Remove conflicting third-party tracking plugins",
            "Deploy native snippet via custom theme functions.php or GTM",
            "Validate single firing per page in Meta Pixel Helper",
            "Check server CPU load reduction in hosting dashboard"
        ],
        tags=["#CleanCode", "#MetaPixel", "#JavaScript", "#WebOptimization", "#DataEngineering"]
    ),
    # Day 14: Class 25 (Google Consent Mode V2)
    CurriculumTopic(
        class_id=25,
        module_category="Privacy Compliance & Analytics",
        title="Google Consent Mode V2: Preserving Attribution Under GDPR & DMA Regulations",
        problem_statement="Missing Google Consent Mode V2 flags (ad_user_data & ad_personalization) blocks audience remarketing and conversion modeling across EEA and global traffic.",
        actionable_tip="Configure GTM with Consent Mode V2 defaults ('denied') before loading tags, then dynamically grant consent upon CMP banner acceptance to unlock Google Behavioral Modeling.",
        code_snippet=(
            "<!-- Default Consent State Before GTM Loads -->\n"
            "<script>\n"
            "  window.dataLayer = window.dataLayer || [];\n"
            "  function gtag(){dataLayer.push(arguments);}\n"
            "  gtag('consent', 'default', {\n"
            "    'ad_storage': 'denied',\n"
            "    'ad_user_data': 'denied',\n"
            "    'ad_personalization': 'denied',\n"
            "    'analytics_storage': 'denied'\n"
            "  });\n"
            "</script>"
        ),
        roi_metric_label="Modeled Conversions",
        roi_metric_value="+18%",
        roi_subtext="Recovered via AI conversion modeling",
        checklist_items=[
            "Inject gtag consent default before GTM container script",
            "Integrate certified CMP banner (Cookiebot / Usercentrics / Stape)",
            "Verify ad_user_data and ad_personalization state in GTM Debug",
            "Check Google Ads conversion action diagnostics for green check"
        ],
        tags=["#ConsentModeV2", "#GDPR", "#GoogleAds", "#PrivacyFirst", "#GA4"]
    ),
    # Day 15: Paid Advertising Strategy (Meta Andromeda 2026)
    CurriculumTopic(
        class_id=26,
        module_category="Paid Advertising Strategy",
        title="Meta Andromeda Algorithm 2026: Structuring Advantage+ Campaigns for Scale",
        problem_statement="Micro-targeting and fragmented ad sets trigger Meta's auction overlap and force ad sets into prolonged learning phase with erratic CPA spikes.",
        actionable_tip="Consolidate budget into broad Advantage+ Shopping Campaigns (ASC) or broad CBO with 3-5 distinct creative angles, letting Meta's Andromeda AI self-optimize.",
        code_snippet=(
            "# Meta Advantage+ Architecture Blueprint:\n"
            "Campaign: CBO (Advantage Campaign Budget) -> 1 Consolidated Ad Set\n"
            "Audience: Broad (Open Age/Gender, Saudi Arabia / GCC, Zero detailed targeting)\n"
            "Creatives Matrix (5 Angles):\n"
            "  - Angle 1: Direct ROI Proof / Case Study Stat Card\n"
            "  - Angle 2: Founder / Operator Video Walkthrough\n"
            "  - Angle 3: 5-Slide Carousel Technical Problem vs Fix\n"
            "  - Angle 4: Social Proof / Verified Student Result\n"
            "  - Angle 5: Urgency / Cohort Deadline Offer"
        ),
        roi_metric_label="Cost Per Acquisition (CPA)",
        roi_metric_value="-31%",
        roi_subtext="Sustained efficiency during budget scale",
        checklist_items=[
            "Consolidate multiple small ad sets into 1 primary scaling campaign",
            "Eliminate overlapping audience exclusions that restrict auction liquidity",
            "Deploy at least 3 distinct creative formats (Video, Static, Carousel)",
            "Feed high-quality CAPI server signals to speed up algorithmic learning"
        ],
        tags=["#MetaAds", "#AdvantagePlus", "#PaidAcquisition", "#MediaBuying", "#GrowthHacking"]
    ),
    # Day 16: Freelancing & High-Ticket Client Acquisition
    CurriculumTopic(
        class_id=27,
        module_category="Freelancing & Client Acquisition",
        title="High-Ticket Client Acquisition Outside Upwork/Fiverr: The Technical Audit Hook",
        problem_statement="Competing strictly on freelance marketplaces creates race-to-the-bottom pricing, high platform fees (10-20%), and client micromanagement.",
        actionable_tip="Pitch prospective eCommerce founders on LinkedIn using a 3-minute Loom video revealing their broken Meta Pixel Event Match Quality or missing Consent Mode V2, charging $500-$2,000 retainer.",
        code_snippet=(
            "// The 3-Minute Audit Checklist for Client Outreach:\n"
            "1. Inspect website with Meta Pixel Helper (check for duplicate events)\n"
            "2. Inspect Network Tab for 'collect' & 'google-analytics' (verify GA4 & CAPI)\n"
            "3. Check cookies for _fbp lifespan (if 24 hours -> ITP data loss confirmed!)\n"
            "4. Record 3-minute Loom: 'Hey [Name], noticed your pixel loses 35% of checkout data...'\n"
            "5. CTA: 'I can deploy Stape server container to recover your tracking in 48 hours.'"
        ),
        roi_metric_label="Average Deal Size",
        roi_metric_value="$1,250",
        roi_subtext="Retainer pricing vs $50 gig bidding",
        checklist_items=[
            "Identify eCommerce stores spending $5k+/mo on Meta/Google Ads",
            "Audit tracking health using Chrome Developer Tools and Pixel Helper",
            "Send personalized audit Loom with zero sales fluff",
            "Receive international payment directly via Wise or Payoneer business account"
        ],
        tags=["#Freelancing", "#ClientHunting", "#HighTicketSales", "#Wise", "#Payoneer"]
    )
]


class CurriculumEngine:
    """Manages the master curriculum syllabus, topic rotation, and content alignment."""

    def __init__(self, curriculum: List[CurriculumTopic] = None):
        self.curriculum = curriculum or CURRICULUM_BANK

    def get_topic_by_day(self, day_number: int) -> CurriculumTopic:
        """Selects curriculum topic mapped to day number with deterministic cyclic rotation."""
        idx = (day_number - 1) % len(self.curriculum)
        return self.curriculum[idx]

    def get_as_research_topic(self, day_number: int) -> ResearchTopic:
        """Translates a curriculum topic into a standard ResearchTopic for the multi-agent pipeline."""
        ct = self.get_topic_by_day(day_number)
        summary = (
            f"Module: {ct.module_category} (Class {ct.class_id}). "
            f"Problem: {ct.problem_statement} "
            f"Actionable Tip: {ct.actionable_tip} "
            f"Key Metric: {ct.roi_metric_label} {ct.roi_metric_value} ({ct.roi_subtext})."
        )
        return ResearchTopic(
            id=f"syllabus_class_{ct.class_id}_day_{day_number}",
            title=ct.title,
            url=f"internal://syllabus/class_{ct.class_id}",
            source=f"Advance Digital Marketing Master Syllabus (Class {ct.class_id})",
            score=980,
            num_comments=145,
            summary=summary,
            created_utc=0.0
        )
