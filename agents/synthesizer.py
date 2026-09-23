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
from agents.curriculum_engine import CurriculumEngine

load_dotenv()


class ContentSynthesizer:
    """Generates technical carousel slides, captions, and first comments with self-learning exemplars."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = None
        self.mock_mode = True
        self.curriculum_engine = CurriculumEngine()

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
                    "cta_text": "📌 Save This Blueprint  •  Follow Tipu Sultan for Daily Tracking Architecture"
                }}
            ],
            "post_caption": "string",
            "hashtags": ["#WebAnalytics", "#DataDrivenGrowth"],
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
                err_msg = str(e)
                print(f"[Synthesizer] Gemini API call attempt {attempt + 1}/3 notice: {err_msg[:120]}")
                if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                    print("[Synthesizer] Gemini daily quota reached. Fast-switching to high-fidelity curriculum generator.")
                    raise e
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
        """Deterministic, production-grade template synthesizer dynamically mapped to Master Syllabus classes."""
        badge = f"Tipu Sultan | AI & Data Growth Architect • Day {day_number:02d}"

        # Fetch syllabus lesson strictly anchored to day number
        ct = self.curriculum_engine.get_topic_by_day(day_number)

        clean_title = ct.title.replace("\n", " ").strip()
        if len(clean_title) > 65:
            clean_title = clean_title[:62] + "..."

        revision_note = ""
        if revision_request:
            revision_note = f"\n[Editor Note: {revision_request}]"

        # Dynamically build checklist bullets
        checklist_bullets = [f"{i+1}. {item}" for i, item in enumerate(ct.checklist_items[:4])]
        if not checklist_bullets:
            checklist_bullets = [
                f"1. Audit baseline tracking signals in {ct.module_category}",
                "2. Deploy production-grade snippet via GTM container",
                "3. Verify payload parameters in real-time debugger",
                "4. Monitor conversion match score inside platform console"
            ]

        slides = [
            Slide(
                slide_number=1,
                badge=badge,
                title=clean_title,
                subtitle=f"Class {ct.class_id} Blueprint • {ct.module_category}",
                body_bullets=[
                    f"Core Problem: {ct.problem_statement[:95]}...",
                    f"Architecture Fix: {ct.actionable_tip[:95]}...",
                    "Engineered for Technical Marketers, Media Buyers & Growth Founders."
                ],
                cta_text="Swipe for Architecture Blueprint →"
            ),
            Slide(
                slide_number=2,
                badge=badge,
                title="The Production Bottleneck",
                subtitle=f"Why standard implementations fail in {ct.module_category}",
                body_bullets=[
                    f"1. Signal Loss: {ct.problem_statement}",
                    "2. Algorithmic Misalignment: Degraded signals force ad bidders into erratic CPA spikes.",
                    "3. Tracking Blind Spot: Missing attribution breaks budget scaling confidence."
                ]
            ),
            Slide(
                slide_number=3,
                badge=badge,
                title="The Implementation Blueprint",
                subtitle=f"Class {ct.class_id} Executable Code Architecture" + revision_note,
                body_bullets=[
                    ct.actionable_tip,
                    "Production-tested snippet ready for direct GTM / CMS deployment."
                ],
                code_snippet=ct.code_snippet
            ),
            Slide(
                slide_number=4,
                badge=badge,
                title="Measurable Business ROI",
                subtitle="Engineering Precision Translating to Ad & Revenue Performance",
                body_bullets=[
                    f"Primary benchmark: {ct.roi_metric_label} achieving {ct.roi_metric_value}.",
                    f"Signal uplift: {ct.roi_subtext}.",
                    "Eliminating data blind spots enables confident ad budget scaling."
                ],
                metrics=[
                    SlideMetric(label=ct.roi_metric_label, value=ct.roi_metric_value, subtext=ct.roi_subtext),
                    SlideMetric(label="Data Integrity", value="99.9%", subtext="deterministic audit"),
                    SlideMetric(label="ROAS Impact", value="3.5x - 5.2x", subtext="scale-ready attribution")
                ]
            ),
            Slide(
                slide_number=5,
                badge=badge,
                title="Implementation Checklist",
                subtitle=f"Production Deployment Guide • Class {ct.class_id}",
                body_bullets=checklist_bullets,
                cta_text="Save This Blueprint  •  Follow Tipu Sultan for Daily Tracking Architecture"
            )
        ]

        post_caption = (
            f"🚀 {clean_title} ({badge})\n\n"
            f"Most media buyers obsess over creatives while silently losing conversion revenue to broken tracking architecture.\n\n"
            f"📌 The Core Bottleneck (Class {ct.class_id}):\n"
            f"{ct.problem_statement}\n\n"
            f"⚡ The Technical Fix:\n"
            f"{ct.actionable_tip}\n\n"
            f"📊 Proven Benchmark:\n"
            f"• {ct.roi_metric_label}: {ct.roi_metric_value} ({ct.roi_subtext})\n"
            f"• Data Integrity: 99.9% verified\n\n"
            f"👉 Swipe through the 5-slide visual carousel above for the exact code implementation, GTM DataLayer setup, and deployment checklist.\n\n"
            f"📌 Save this blueprint for your next tracking deployment.\n"
            f"👤 Follow Tipu Sultan for daily enterprise breakdowns of Web Analytics, Meta CAPI & AI Growth Architecture."
        )

        first_comment = (
            f"💬 Discussion for Growth Marketers & Analytics Engineers:\n"
            f"When managing {ct.module_category}, what is your biggest production bottleneck right now? "
            f"Have you faced signal drops or tracking discrepancy? Drop your experience below and let's troubleshoot 👇"
        )

        tags = list(dict.fromkeys(ct.tags + ["#TipuSultan", "#GrowthArchitect", "#WebAnalytics"]))

        return CarouselContent(
            day_number=day_number,
            topic_headline=clean_title,
            slides=slides,
            post_caption=post_caption,
            hashtags=tags,
            first_comment=first_comment
        )
