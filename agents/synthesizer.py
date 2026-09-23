"""Synthesizer Agent: Generates 5-slide technical carousels with historical feedback injection.

Leverages Gemini Pro / 2.5 Flash via google-genai SDK, injecting high-performing exemplars
from the SQLite RLSF memory loop. Formatted for the 'Marketer → GenAI Engineer' persona.
"""

import os
import json
import time
import warnings
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Suppress harmless AFC notification on generate_content
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", category=UserWarning)

from state import ResearchTopic, CarouselContent, Slide, SlideMetric

load_dotenv()


class ContentSynthesizer:
    """Generates technical carousel slides, captions, and first comments with self-learning exemplars."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = None
        self.mock_mode = True

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.mock_mode = False
                print("[Synthesizer] Live Gemini client authenticated successfully.")
            except Exception as e:
                print(f"[Synthesizer] Warning: Failed to initialize google.genai Client: {e}")
                self.mock_mode = True

    def synthesize_carousel(
        self,
        topic: ResearchTopic,
        exemplars: List[Dict[str, Any]] = None,
        day_number: int = 14,
        revision_request: Optional[str] = None,
        existing_carousel: Optional[CarouselContent] = None,
    ) -> CarouselContent:
        """Synthesizes the complete 5-slide carousel package."""
        exemplars = exemplars or []

        # If live API is available and not in mock mode, attempt Gemini generation
        if not self.mock_mode and self.client:
            try:
                return self._generate_with_gemini(
                    topic, exemplars, day_number, revision_request, existing_carousel
                )
            except Exception as e:
                print(f"[Synthesizer] Gemini API call error: {e}. Falling back to robust generator.")

        # Robust generation (used in mock mode or fallback)
        return self._generate_structured_content(
            topic, exemplars, day_number, revision_request, existing_carousel
        )

    def _generate_with_gemini(
        self,
        topic: ResearchTopic,
        exemplars: List[Dict[str, Any]],
        day_number: int,
        revision_request: Optional[str],
        existing_carousel: Optional[CarouselContent],
    ) -> CarouselContent:
        """Calls Gemini Pro / Flash using google-genai SDK."""
        exemplar_text = ""
        if exemplars:
            exemplar_text = "HISTORICAL TOP-PERFORMING POSTS (RLSF Exemplars):\n"
            for ex in exemplars:
                exemplar_text += f"- Title: {ex.get('topic_title')} (Score: {ex.get('engagement_score')})\n  Hook: {ex.get('hook_text')}\n"

        revision_text = ""
        if revision_request and existing_carousel:
            revision_text = f"""
            CRITICAL REVISION INSTRUCTION FROM HUMAN EDITOR:
            "{revision_request}"
            Apply this specific change while preserving the core 5-slide structure.
            Previous JSON state: {existing_carousel.model_dump_json()}
            """

        prompt = f"""
        You are Tipu Sultan, an elite AI-Driven & Data-Driven Growth Architect.
        Your brand badge is: "Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}".
        Your target audience: Technical digital marketers, eCommerce brand founders, media buyers, CMOs, and analytics engineers.

        CRITICAL ANTI-SPAM RULE (ZERO EXTERNAL LINKS):
        Social media algorithms heavily penalize posts containing external links.
        DO NOT include any website URLs (http://, https://, .com, .io, .github.io, etc.) anywhere in the post_caption, slides, or first_comment.
        Drive all authority and discovery purely through author branding: "Follow Tipu Sultan for daily tracking breakdowns" and conversation-starting discussion questions.

        MISSION:
        Create a high-retention 5-slide technical carousel based on this Master Syllabus topic:
        Headline: {topic.title}
        Source: {topic.source}
        Summary: {topic.summary}

        {exemplar_text}
        {revision_text}

        SLIDE REQUIREMENTS (Exactly 5 slides):
        - Slide 1: High-contrast Hook + Author Brand Badge ("Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}") + Subtitle
        - Slide 2: The Core Tracking / Marketing Bottleneck (e.g. 30-40% data loss, iOS 14.5 ITP, duplicate conversions, low match quality)
        - Slide 3: The Architecture Diagram / Code Solution (clean, working JavaScript snippet for GTM DataLayer, DOM scraping, Stape CAPI, or Consent Mode V2)
        - Slide 4: Measurable Business Value & Ads ROI (2-3 concrete metrics: Event Match Quality 9.2/10, +38% Recovered Data, ROAS Multiplier, CPA reduction)
        - Slide 5: Summary Checklist + "Save This Blueprint  •  Follow Tipu Sultan for Daily Tracking Architecture" CTA (NO URLS)

        Also generate:
        - post_caption: High-converting LinkedIn/Facebook/Instagram post body with emojis, line breaks, technical breakdown, clear bullet points, sign-off signature, and NO external links.
        - hashtags: 5-8 relevant tags (#WebAnalytics, #ServerSideTracking, #MetaCAPI, #GoogleTagManager, #GA4, #TipuSultan, #GrowthArchitect).
        - first_comment: High-engagement conversation starter asking a technical question to prompt comments and discussion (NO external links!).

        Output ONLY valid JSON matching this schema:
        {{
            "day_number": {day_number},
            "topic_headline": "string",
            "slides": [
                {{
                    "slide_number": 1,
                    "badge": "Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}",
                    "title": "string",
                    "subtitle": "string",
                    "body_bullets": ["string"],
                    "code_snippet": null,
                    "metrics": [],
                    "cta_text": "Swipe for Architecture →"
                }},
                {{
                    "slide_number": 2,
                    "badge": "Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}",
                    "title": "The Tracking Bottleneck",
                    "subtitle": "Why standard browser pixels lose 35%+ of data",
                    "body_bullets": ["string", "string", "string"],
                    "code_snippet": null,
                    "metrics": [],
                    "cta_text": null
                }},
                {{
                    "slide_number": 3,
                    "badge": "Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}",
                    "title": "Architecture & Implementation",
                    "subtitle": "How the solution works under the hood",
                    "body_bullets": ["string"],
                    "code_snippet": "javascript code string",
                    "metrics": [],
                    "cta_text": null
                }},
                {{
                    "slide_number": 4,
                    "badge": "Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}",
                    "title": "Measurable Business ROI",
                    "subtitle": "Bridging Engineering Precision with Ad Performance",
                    "body_bullets": ["string"],
                    "metrics": [
                        {{"label": "Event Match Quality", "value": "9.4 / 10", "subtext": "via CAPI server enrich"}},
                        {{"label": "Data Recovery", "value": "+38%", "subtext": "post-iOS 14.5"}}
                    ],
                    "cta_text": null
                }},
                {{
                    "slide_number": 5,
                    "badge": "Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}",
                    "title": "Implementation Checklist",
                    "subtitle": "Production Deployment Guide",
                    "body_bullets": ["string", "string", "string"],
                    "code_snippet": null,
                    "metrics": [],
                    "cta_text": "📌 Save for Later | Case Studies: sultantipu199.github.io/sultan-growth"
                }}
            ],
            "post_caption": "string",
            "hashtags": ["#LangGraph", "#GenAI"],
            "first_comment": "string"
        }}
        """

        # Model selection: gemini-3.6-flash (recommended modern standard)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        response = None
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                if response and response.text:
                    break
            except Exception as e:
                print(f"[Synthesizer] Gemini API call attempt {attempt + 1}/3 warning: {e}")
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                else:
                    raise e

        raw_text = response.text.strip()
        # Clean markdown wrappers if any
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]

        parsed = json.loads(raw_text.strip())
        return CarouselContent.model_validate(parsed)

    def _generate_structured_content(
        self,
        topic: ResearchTopic,
        exemplars: List[Dict[str, Any]],
        day_number: int,
        revision_request: Optional[str],
        existing_carousel: Optional[CarouselContent],
    ) -> CarouselContent:
        """Deterministic, production-grade template synthesizer for Tipu Sultan AI & Data Growth Architecture."""
        badge = f"Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}"

        # Clean title
        clean_title = topic.title.replace("\n", " ").strip()
        if len(clean_title) > 65:
            clean_title = clean_title[:62] + "..."

        # Executable JavaScript / DataLayer snippet tailored to tracking & marketing
        code_body = (
            "// Server-Side First-Party CAPI & DataLayer Event Deduplication\n"
            "window.dataLayer = window.dataLayer || [];\n"
            "var eventId = 'order_' + ({{dlv - order_id}} || Date.now());\n\n"
            "// 1. Browser Pixel Dispatch with Unique Event ID\n"
            "fbq('track', 'Purchase', {\n"
            "  value: {{dlv - purchase_value}},\n"
            "  currency: 'USD'\n"
            "}, {eventID: eventId});\n\n"
            "// 2. Server CAPI Sync (Stape.io / GTM Server Container)\n"
            "dataLayer.push({\n"
            "  event: 'server_purchase',\n"
            "  event_id: eventId,\n"
            "  user_data: {\n"
            "    em: {{sha256_email}},\n"
            "    ph: {{sha256_phone}}\n"
            "  }\n"
            "});"
        )

        # Apply revision if specified
        revision_note = ""
        if revision_request:
            revision_note = f"\n[Editor Note: {revision_request}]"

        slides = [
            Slide(
                slide_number=1,
                badge=badge,
                title="Stop Losing 35%+ of Ad Revenue to Broken Tracking.",
                subtitle=f"How We Scaled: {clean_title}",
                body_bullets=[
                    "Most eCommerce brands rely on fragile client-side browser pixels.",
                    "Safari ITP, iOS 14.5+, and ad blockers destroy up to 40% of conversion signals.",
                    "Here is the exact AI-driven server-side tracking architecture we deploy."
                ],
                cta_text="Swipe for Architecture Blueprint →"
            ),
            Slide(
                slide_number=2,
                badge=badge,
                title="The Data Loss Bottleneck",
                subtitle="Why standard browser pixels silently fail in 2026",
                body_bullets=[
                    "ITP Cookie Degradation: Safari caps client cookies at 24 hours, breaking 7-day attribution.",
                    "Ad Blockers & VPNs: Over 35% of high-intent shoppers block standard third-party tracking scripts.",
                    "Auction Misalignment: When Meta and Google receive degraded signals, Smart Bidding underbids on high-value buyers."
                ]
            ),
            Slide(
                slide_number=3,
                badge=badge,
                title="The Architecture Breakdown",
                subtitle="Stape.io Server Container + First-Party CAPI Sync" + revision_note,
                body_bullets=[
                    "First-party sub-domain routing restores full 365-day cookie persistence.",
                    "Deterministic event_id deduplication guarantees 0% double-counting in Ads Manager."
                ],
                code_snippet=code_body
            ),
            Slide(
                slide_number=4,
                badge=badge,
                title="Measurable Business ROI",
                subtitle="Bridging Server-Side Engineering with Commercial ROAS",
                body_bullets=[
                    "Enhanced signal match scores unlock aggressive Meta Advantage+ budget scaling.",
                    "Zero data loss eliminates blind ad spend and lowers Blended Customer Acquisition Cost."
                ],
                metrics=[
                    SlideMetric(label="Event Match Quality", value="9.4 / 10", subtext="via CAPI server enrich"),
                    SlideMetric(label="Attributed Revenue", value="+38%", subtext="recovered post-iOS 14.5"),
                    SlideMetric(label="Blended ROAS", value="4.8x", subtext="across verified accounts")
                ]
            ),
            Slide(
                slide_number=5,
                badge=badge,
                title="Implementation Checklist",
                subtitle="Production Deployment Guide",
                body_bullets=[
                    "1. Deploy custom domain CNAME record pointing to GTM Server Container.",
                    "2. Configure unique event_id generation across both browser and server tags.",
                    "3. Hash user email and phone with SHA-256 for Advanced Matching parameters.",
                    "4. Audit live signals using Meta Events Manager Test Events tool."
                ],
                cta_text="Save This Blueprint  •  Follow Tipu Sultan for Daily Tracking Architecture"
            )
        ]

        post_caption = (
            f"🚀 Most media buyers obsess over ad creative while silently losing 35%+ of their conversion data to broken tracking.\n\n"
            f"When your tracking signals degrade:\n"
            f"1️⃣ Safari ITP drops cookie lifespan to 24 hours (killing 7-day click attribution).\n"
            f"2️⃣ Ad blockers wipe out 30-40% of standard browser pixel events.\n"
            f"3️⃣ Meta Andromeda and Google Smart Bidding algorithms underbid because they cannot see who actually bought.\n\n"
            f"In today's breakdown ({badge}), we dissect the exact architecture: {clean_title}.\n\n"
            f"👉 Swipe through the 5-slide visual carousel above for the exact JavaScript implementation, GTM DataLayer setup, and measurable ROI benchmarks.\n\n"
            f"📌 Save this blueprint for your next tracking deployment.\n"
            f"👤 Follow Tipu Sultan for daily enterprise breakdowns of Web Analytics, Meta CAPI & AI Growth Architecture.\n\n"
            f"💡 What does your current Event Match Quality score look like in Meta Events Manager? Let's discuss below!"
        )

        first_comment = (
            f"💬 Discussion for Growth Marketers & Analytics Engineers:\n"
            f"What is currently your biggest tracking bottleneck — Safari 24-hour cookie drop, Meta CAPI event deduplication mismatch, or Consent Mode V2 setup?\n\n"
            f"Drop your experience below and let's troubleshoot 👇"
        )

        hashtags = [
            "#WebAnalytics",
            "#ServerSideTracking",
            "#MetaCAPI",
            "#GoogleTagManager",
            "#GA4",
            "#TipuSultan",
            "#GrowthArchitect",
            "#DataDrivenMarketing"
        ]

        return CarouselContent(
            day_number=day_number,
            topic_headline=clean_title,
            slides=slides,
            post_caption=post_caption,
            hashtags=hashtags,
            first_comment=first_comment
        )
