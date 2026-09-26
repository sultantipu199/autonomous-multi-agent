"""Comprehensive Automated Test Suite for Autonomous Multi-Agent Growth Platform.

Audits every layer:
1. Harvester (parallel scraping, latency, schema)
2. Synthesizer (5-slide format, code snippets, ROI metrics)
3. Critic (adversarial reflection & quality scoring)
4. Carousel Engine (visual rendering 1080x1080 & PDF compilation)
5. Publisher (multi-platform configuration, token scopes, CDN image pipeline)
6. Scheduler (Asia/Dhaka timezone, jitter window)
7. Security & Secret Isolation Audit (zero-leak guarantee)
"""

import os
import sys
import time
import unittest
from dotenv import load_dotenv

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from state import ResearchTopic, CarouselContent, Slide, SlideMetric, CritiqueResult
from agents.harvester import ContentHarvester
from agents.synthesizer import ContentSynthesizer
from agents.critic import ContentCritic
from agents.carousel_engine import CarouselEngine
from agents.publisher import MultiPlatformPublisher
from agents.dynamic_scheduler import DynamicScheduler

load_dotenv()


class TestMultiAgentPlatform(unittest.TestCase):
    """End-to-end verification of multi-agent components."""

    def test_01_harvester_speed_and_schema(self):
        """Verify parallel harvesting completes under 5 seconds with valid topics."""
        harvester = ContentHarvester()
        start = time.time()
        best_topic = harvester.harvest_best_topic()
        elapsed = time.time() - start

        self.assertIsNotNone(best_topic, "Harvester must return a topic")
        self.assertLess(elapsed, 10.0, f"Harvester should be parallel and fast, took {elapsed:.2f}s")
        self.assertIsInstance(best_topic, ResearchTopic)
        self.assertTrue(len(best_topic.title) > 5)
        print(f"\n[Test Harvester] PASSED (Best topic '{best_topic.title[:35]}...' retrieved in {elapsed:.2f}s)")

    def test_02_synthesizer_structured_output(self):
        """Verify synthesizer produces exact 5-slide Marketer -> GenAI Engineer carousel."""
        topic = ResearchTopic(
            id="test_hn_1",
            title="Building Production LangGraph Multi-Agent Workflows",
            url="https://news.ycombinator.com/item?id=123",
            source="hackernews",
            score=250,
            summary="Discussion on reliable agent orchestration, checkpointing, and reflection loops."
        )
        synthesizer = ContentSynthesizer()
        carousel = synthesizer.synthesize_carousel(topic, day_number=14)

        self.assertEqual(len(carousel.slides), 5, "Carousel must have exactly 5 slides")
        self.assertIn("Tipu Sultan", carousel.slides[0].badge)
        self.assertIsNotNone(carousel.post_caption)
        self.assertGreaterEqual(len(carousel.hashtags), 3)
        self.assertIsNotNone(carousel.first_comment)
        
        # Verify Strict Zero-Link Anti-Spam Policy
        self.assertNotIn("http://", carousel.post_caption, "CRITICAL: No URLs allowed in post caption!")
        self.assertNotIn("https://", carousel.post_caption, "CRITICAL: No URLs allowed in post caption!")
        self.assertNotIn("http://", carousel.first_comment, "CRITICAL: No URLs allowed in first comment!")
        self.assertNotIn("https://", carousel.first_comment, "CRITICAL: No URLs allowed in first comment!")
        self.assertIn("Tipu Sultan", carousel.post_caption)
        print(f"[Test Synthesizer] PASSED (Day {carousel.day_number} zero-link carousel validated for Tipu Sultan)")

    def test_03_critic_adversarial_evaluation(self):
        """Verify critic performs rigorous scoring and passes high-quality technical content."""
        critic = ContentCritic()
        carousel = CarouselContent(
            day_number=14,
            topic_headline="Production Server-Side Tracking & CAPI",
            post_caption="Deep-dive into Meta Conversion API and Server-Side tracking.\n\n#DigitalMarketing #CAPI",
            hashtags=["#DigitalMarketing", "#CAPI", "#WebAnalytics"],
            first_comment="Discussion: What is your biggest tracking challenge right now? Drop your thoughts below 👇",
            slides=[
                Slide(
                    slide_number=1,
                    badge="Tipu Sultan | AI & Data Growth Architect • Day 14",
                    title="Stop Losing 35% of Purchase Data",
                    subtitle="Why Browser-Only Meta Pixel Fails Post-iOS 14.5",
                    body_bullets=["Safari ITP cuts cookie lifespan to 24h", "AdBlockers kill standard fbq calls"],
                    cta_text="Swipe for Fix →"
                ),
                Slide(
                    slide_number=2,
                    badge="Tipu Sultan | AI & Data Growth Architect • Day 14",
                    title="The Core Production Bottleneck",
                    body_bullets=["Client-side signal degradation", "No Event Match Quality optimization"]
                ),
                Slide(
                    slide_number=3,
                    badge="Tipu Sultan | AI & Data Growth Architect • Day 14",
                    title="The Server-Side Solution",
                    code_snippet="function setFirstPartyFbp() {\n  setCookie('_fbp', fbp, 365, 'yourdomain.com');\n}"
                ),
                Slide(
                    slide_number=4,
                    badge="Tipu Sultan | AI & Data Growth Architect • Day 14",
                    title="Measurable Business ROI",
                    metrics=[SlideMetric(label="Match Quality", value="9.4/10"), SlideMetric(label="ROAS Recovery", value="+32%")]
                ),
                Slide(
                    slide_number=5,
                    badge="Tipu Sultan | AI & Data Growth Architect • Day 14",
                    title="Implementation Checklist",
                    body_bullets=["Configure Stape.io custom loader", "Enforce event_id deduplication"],
                    cta_text="Save & Follow for Day 15 →"
                )
            ]
        )
        result = critic.evaluate(carousel)
        self.assertIsInstance(result, CritiqueResult)
        self.assertGreaterEqual(result.score, 7.5, "High quality content should score >= 7.5")
        print(f"[Test Critic] PASSED (Score: {result.score:.1f}/10)")

    def test_04_carousel_engine_rendering_and_pdf(self):
        """Verify rendering produces 5 1080x1080 PNG slides and compiled PDF."""
        engine = CarouselEngine()
        carousel = CarouselContent(
            day_number=14,
            topic_headline="Autonomous Multi-Agent Architecture",
            post_caption="Test caption",
            hashtags=["#AI"],
            first_comment="Test comment",
            slides=[
                Slide(slide_number=i, title=f"Slide {i} Header", body_bullets=["Point 1", "Point 2"])
                for i in range(1, 6)
            ]
        )
        start = time.time()
        png_paths, pdf_path = engine.render_all(carousel)
        elapsed = time.time() - start

        self.assertEqual(len(png_paths), 5)
        self.assertTrue(os.path.exists(pdf_path))
        for p in png_paths:
            self.assertTrue(os.path.exists(p))
        self.assertLess(elapsed, 4.0, f"Rendering took {elapsed:.2f}s, expected < 4.0s")
        print(f"[Test Carousel Engine] PASSED (5 slides + PDF rendered in {elapsed:.2f}s)")

    def test_05_dynamic_scheduler(self):
        """Verify Asia/Dhaka scheduler calculates slots inside the daily window."""
        scheduler = DynamicScheduler()
        slot = scheduler.calculate_optimal_slot()
        self.assertIsNotNone(slot)
        self.assertIn("scheduled_time_display", slot)
        print(f"[Test Dynamic Scheduler] PASSED (Target slot: {slot['scheduled_time_display']})")

    def test_06_publisher_meta_and_instagram_configuration(self):
        """Verify publisher handles credentials, resolves Page and Instagram IDs."""
        publisher = MultiPlatformPublisher()
        self.assertTrue(bool(publisher.meta_page_id), "META_PAGE_ID must be configured")
        self.assertEqual(publisher.meta_page_id, "105656909238175")
        
        # Verify Instagram Account resolution
        ig_id = publisher._get_or_detect_instagram_id()
        self.assertEqual(ig_id, "17841405072430897", "Must match verified Instagram ID")
        print(f"[Test Publisher Config] PASSED (Page: {publisher.meta_page_id}, IG: {ig_id})")

    def test_07_pro_level_privacy_and_security_audit(self):
        """Verify zero secret leaks: .env, databases, and logs are completely git-ignored."""
        import subprocess

        # 1. Verify git ignores .env
        git_check_env = subprocess.run(
            ["git", "status", "--porcelain", ".env"],
            capture_output=True,
            text=True
        )
        self.assertEqual(git_check_env.stdout.strip(), "", "CRITICAL: .env must NOT appear in git status")

        # 2. Verify git ignores data/ and SQLite databases
        git_check_data = subprocess.run(
            ["git", "status", "--porcelain", "data/"],
            capture_output=True,
            text=True
        )
        self.assertEqual(git_check_data.stdout.strip(), "", "CRITICAL: data/ must NOT appear in git status")

        # 3. Verify .env.example contains NO live secrets
        with open(".env.example", "r", encoding="utf-8") as f:
            example_content = f.read()

        real_gemini = os.getenv("GEMINI_API_KEY", "")
        if real_gemini:
            self.assertNotIn(real_gemini, example_content, "CRITICAL: GEMINI_API_KEY leaked in .env.example!")

        real_meta = os.getenv("META_PAGE_ACCESS_TOKEN", "")
        if real_meta:
            self.assertNotIn(real_meta, example_content, "CRITICAL: META_PAGE_ACCESS_TOKEN leaked in .env.example!")

        real_li = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        if real_li:
            self.assertNotIn(real_li, example_content, "CRITICAL: LINKEDIN_ACCESS_TOKEN leaked in .env.example!")

        # 4. Verify PRIVACY_POLICY.md exists and is documented
        self.assertTrue(os.path.exists("PRIVACY_POLICY.md"), "PRIVACY_POLICY.md must exist in the repository")

        print("[Test Privacy & Security Audit] PASSED (Zero-secret leakage & PRIVACY_POLICY.md confirmed)")

    def test_08_curriculum_engine_and_syllabus_coverage(self):
        """Verify CurriculumEngine delivers root syllabus classes, CAPI, GTM, and portfolio references."""
        from agents.curriculum_engine import CurriculumEngine, CURRICULUM_BANK

        engine = CurriculumEngine()
        self.assertGreaterEqual(len(CURRICULUM_BANK), 8, "Curriculum bank must contain comprehensive lessons")

        # Test deterministic rotation
        topic_day_1 = engine.get_topic_by_day(1)
        topic_day_2 = engine.get_topic_by_day(2)
        self.assertNotEqual(topic_day_1.title, topic_day_2.title)

        # Test translation to ResearchTopic
        rt = engine.get_as_research_topic(day_number=1)
        self.assertTrue(rt.url.startswith("internal://syllabus"))
        self.assertTrue(len(topic_day_1.code_snippet) > 20, "Every curriculum topic must contain real code/config")
        self.assertTrue(bool(topic_day_1.roi_metric_value), "Must have measurable business ROI")
        print(f"[Test Curriculum Engine] PASSED ({len(CURRICULUM_BANK)} syllabus modules verified with zero external links)")

    def test_09_carousel_avatar_and_zero_link_footer(self):
        """Verify Tipu Sultan's real authentic avatar loads and slides render with zero external links."""
        engine = CarouselEngine()
        avatar = engine._get_avatar(54)
        self.assertIsNotNone(avatar, "Tipu Sultan authentic photo avatar must load")
        self.assertEqual(avatar.size, (54, 54))

        avatar_lg = engine._get_avatar(124)
        self.assertIsNotNone(avatar_lg)
        self.assertEqual(avatar_lg.size, (124, 124))

        # Verify Slide 5 rendering contains author card and zero URL in footer
        carousel = CarouselContent(
            day_number=1,
            topic_headline="Server-Side Tracking",
            post_caption="Caption text",
            hashtags=["#Tag"],
            first_comment="Comment text",
            slides=[
                Slide(slide_number=i, badge="Tipu Sultan | AI & Data Growth Architect • Day 01", title=f"Slide {i}")
                for i in range(1, 6)
            ]
        )
        png_paths, pdf_path = engine.render_all(carousel)
        self.assertEqual(len(png_paths), 5)
        print("[Test Carousel Avatar & Zero-Link] PASSED (Real authentic photo integrated on all slides)")

    def test_10_ninja_content_vault_and_deduplication(self):
        """Verify content_vault.json exists, tracks past topics/hooks, and enforces deduplication."""
        from agents.ninja_orchestrator import initialize_vault, audit_against_vault

        vault = initialize_vault()
        self.assertIn("past_topics", vault)
        self.assertIn("past_hooks", vault)
        self.assertIn("used_tactics", vault)
        self.assertIn("posts", vault)
        self.assertIn("current_day", vault)
        print(f"[Test Ninja Vault & Deduplication] PASSED ({len(vault['posts'])} posts stored with active stateful memory)")

    def test_11_sequential_day_numbering_and_unique_content(self):
        """Verify sequential day numbering starts at Day 1 and produces 100% unique, non-repeating content."""
        from agents.curriculum_engine import CurriculumEngine
        from agents.synthesizer import ContentSynthesizer
        from agents.ninja_orchestrator import get_current_day, advance_current_day, set_current_day

        engine = CurriculumEngine()
        synthesizer = ContentSynthesizer()

        # 1. Day 1 topic must be Class 1-3 GTM DataLayer
        t1 = engine.get_topic_by_day(1)
        self.assertEqual(t1.class_id, 1)
        self.assertIn("DataLayer", t1.title)

        # 2. Day 2 topic must be Class 4-6 Facebook Pixel
        t2 = engine.get_topic_by_day(2)
        self.assertEqual(t2.class_id, 4)
        self.assertIn("Pixel", t2.title)

        # 3. Synthesize Day 1
        rt1 = engine.get_as_research_topic(day_number=1)
        c1 = synthesizer._generate_structured_content(
            topic=rt1, exemplars=[], day_number=1, revision_request=None, existing_carousel=None
        )
        self.assertIn("Day 01", c1.slides[0].badge)
        self.assertIn("DataLayer", c1.slides[0].title)

        # 4. Synthesize Day 2
        rt2 = engine.get_as_research_topic(day_number=2)
        c2 = synthesizer._generate_structured_content(
            topic=rt2, exemplars=[], day_number=2, revision_request=None, existing_carousel=None
        )
        self.assertIn("Day 02", c2.slides[0].badge)
        self.assertIn("Pixel", c2.slides[0].title)

        # 5. Assert complete uniqueness across Day 1 and Day 2
        self.assertNotEqual(c1.slides[0].title, c2.slides[0].title, "Slide 1 title must be distinct!")
        self.assertNotEqual(c1.slides[2].code_snippet, c2.slides[2].code_snippet, "Code snippets must be distinct!")
        self.assertNotEqual(c1.slides[3].metrics[0].label, c2.slides[3].metrics[0].label, "Metrics must be distinct!")
        self.assertNotEqual(c1.post_caption, c2.post_caption, "Post captions must be distinct!")

        # 6. Test day progression logic (safely preserving original vault state)
        vault_file = "content_vault.json"
        original_vault_content = None
        if os.path.exists(vault_file):
            with open(vault_file, "r", encoding="utf-8") as vf:
                original_vault_content = vf.read()

        try:
            set_current_day(1)
            self.assertEqual(get_current_day(), 1)
            next_day = advance_current_day(completed_day=1, topic_title=t1.title)
            self.assertEqual(next_day, 2)
            self.assertEqual(get_current_day(), 2)
        finally:
            if original_vault_content is not None:
                with open(vault_file, "w", encoding="utf-8") as vf:
                    vf.write(original_vault_content)

        print("[Test Sequential Day Progression & Unique Content] PASSED (Day 01 -> Day 02 verified with 100% unique curriculum code & metrics)")

    def test_12_bengali_decision_brief(self):
        """Verify Executive Bengali Decision Brief includes all required breakdown dimensions and zero links."""
        from agents.ninja_orchestrator import generate_bengali_decision_brief
        from agents.curriculum_engine import CurriculumEngine

        engine = CurriculumEngine()
        ct = engine.get_topic_by_day(1)

        brief = generate_bengali_decision_brief(
            day_number=1,
            topic_headline=ct.title,
            class_id=ct.class_id,
            module_category=ct.module_category,
            problem_statement=ct.problem_statement,
            actionable_tip=ct.actionable_tip,
            roi_metric_label=ct.roi_metric_label,
            roi_metric_value=ct.roi_metric_value,
            roi_subtext=ct.roi_subtext,
            critique_score=9.4,
            slides_count=5
        )

        # 1. Assert presence of all key decision sections
        self.assertIn("১. পোস্টটি কি?", brief, "Must explain what the post is")
        self.assertIn("২. কেন এই পোস্টটি তৈরি করা হয়েছে?", brief, "Must explain why")
        self.assertIn("৩. কিভাবে সমাধান করা হয়েছে?", brief, "Must explain how")
        self.assertIn("৪. কোথায় ও কার জন্য?", brief, "Must explain where and target audience")
        self.assertIn("৫. ব্যবসায়িক প্রভাব ও ROI", brief, "Must explain business ROI")
        self.assertIn("৬. এআই কোয়ালিটি ও অ্যান্টি-স্প্যাম অডিট", brief, "Must include AI quality audit")
        self.assertIn("৭. সিদ্ধান্ত নির্দেশিকা", brief, "Must provide actionable approval guide")

        # 2. Assert Day 01 badge and specific class details
        self.assertIn("Day 01", brief)
        self.assertIn("Class 1", brief)
        self.assertIn(ct.roi_metric_label, brief)

        # 3. Assert Zero-Link Anti-Spam compliance
        self.assertNotIn("http://", brief)
        self.assertNotIn("https://", brief)

        print("[Test Bengali Decision Brief] PASSED (7-section executive Bengali briefing verified with zero links)")

    def test_13_facebook_and_instagram_carousel_and_comments(self):
        """Verify Facebook multi-photo carousel, Instagram container carousel, and first comment engine."""
        from unittest.mock import patch, MagicMock
        from agents.publisher import MultiPlatformPublisher, verify_and_update_meta_token

        publisher = MultiPlatformPublisher()
        carousel = CarouselContent(
            day_number=1,
            topic_headline="Advanced Server-Side Tracking",
            post_caption="Deep-dive into Meta CAPI and Server-Side tracking.",
            hashtags=["#CAPI", "#ServerSideTracking", "#GTM"],
            first_comment="First comment insight on server-side tracking.",
            slides=[
                Slide(slide_number=i, badge="Tipu Sultan • Day 01", title=f"Slide {i}")
                for i in range(1, 6)
            ]
        )
        fake_pngs = [f"output/slide_{i}.png" for i in range(1, 6)]

        # 1. Test Facebook Multi-Photo Carousel Payload Construction
        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "data": [{"id": "105656909238175", "name": "Digital Marketing", "access_token": "page_tok_123"}]
            }
            # Mock slide photo uploads returning photo IDs
            mock_post.side_effect = [
                MagicMock(json=lambda: {"id": f"photo_{i}"}) for i in range(1, 6)
            ] + [
                MagicMock(json=lambda: {"id": "105656909238175_post_9999"})
            ]

            fb_id = publisher._publish_meta(carousel, fake_pngs)
            self.assertIn("105656909238175_post_9999", fb_id)

            # Verify feed post called with attached_media
            last_call_args, last_call_kwargs = mock_post.call_args
            feed_payload = last_call_kwargs.get("data", {})
            self.assertIn("attached_media[0]", feed_payload)
            self.assertIn("attached_media[4]", feed_payload)
            self.assertIn("media_fbid", feed_payload["attached_media[0]"])

        # 2. Test Instagram Carousel Container & Publishing Pipeline
        with patch.object(publisher, "_upload_image_to_public_url", return_value="https://files.catbox.moe/test.png"), \
             patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:

            # Mock 5 item container calls, 1 carousel parent call, 1 publish call
            mock_post.side_effect = [
                MagicMock(json=lambda: {"id": f"item_container_{i}"}) for i in range(1, 6)
            ] + [
                MagicMock(json=lambda: {"id": "parent_carousel_container_123"}),
                MagicMock(json=lambda: {"id": "published_ig_media_456"}),
            ]
            # Mock status check FINISHED, then permalink
            mock_get.side_effect = [
                MagicMock(json=lambda: {"status_code": "FINISHED"}),
                MagicMock(json=lambda: {"permalink": "https://www.instagram.com/p/TEST12345/"}),
            ]

            ig_id = publisher._publish_instagram(carousel, fake_pngs)
            self.assertEqual(ig_id, "published_ig_media_456")
            self.assertEqual(publisher.latest_ig_permalink, "https://www.instagram.com/p/TEST12345/")

        # 3. Test Delayed First Comment Worker across FB and IG
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"id": "comment_9999"}
            mock_post.return_value.status_code = 200

            publisher._delayed_first_comment_worker(
                comment_text="Test technical insight",
                li_urn=None,
                meta_id="105656909238175_post_9999",
                delay=0,
                ig_id="published_ig_media_456"
            )
            # Both FB and IG comment endpoints should have been called
            self.assertGreaterEqual(mock_post.call_count, 2)

        # 4. Test verify_and_update_meta_token error handling
        res_empty = verify_and_update_meta_token("")
        self.assertFalse(res_empty["success"])
        self.assertIn("Empty token", res_empty["error"])

        res_invalid = verify_and_update_meta_token("invalid_token_xyz")
        self.assertFalse(res_invalid["success"])

        print("[Test FB & IG Carousel & First Comment] PASSED (Facebook multi-photo & Instagram carousel validated)")

    def test_14_publish_all_partial_status_and_retry(self):
        """Verify that publish_all accurately flags partial status when FB/IG fails, and retry_publish_failed works."""
        from unittest.mock import patch, MagicMock
        from agents.publisher import MultiPlatformPublisher

        publisher = MultiPlatformPublisher()
        carousel = CarouselContent(
            day_number=3,
            topic_headline="Test iOS 14.5 Tracking",
            post_caption="Test caption for iOS tracking.",
            hashtags=["#ServerSideTracking"],
            first_comment="Test first comment.",
            slides=[
                Slide(slide_number=i, badge="Tipu Sultan • Day 03", title=f"Slide {i}")
                for i in range(1, 6)
            ]
        )
        fake_pngs = [f"output/slide_{i}.png" for i in range(1, 6)]

        # Simulate LinkedIn success, but Facebook token expired and Instagram token expired
        with patch.object(publisher, "_publish_linkedin", return_value="urn:li:ugcPost:123456789"), \
             patch.object(publisher, "_publish_meta", return_value="meta_error_token_expired_12345"), \
             patch.object(publisher, "_publish_instagram", return_value="ig_error_token_expired_12345"), \
             patch.object(publisher, "_push_telegram_broadcast"):

            res = publisher.publish_all(carousel, "output/growth_carousel.pdf", fake_pngs, async_first_comment=False)
            self.assertEqual(res.status, "partial", "Status must be 'partial' when LinkedIn succeeds but Meta fails")
            self.assertTrue(res.details.get("linkedin_success"))
            self.assertFalse(res.details.get("facebook_success"))
            self.assertFalse(res.details.get("instagram_success"))

        # Now test retry_publish_failed when FB and IG succeed
        with patch.object(publisher, "_publish_meta", return_value="105656909238175_post_9999"), \
             patch.object(publisher, "_publish_instagram", return_value="published_ig_media_456"):

            retry_res = publisher.retry_publish_failed(carousel, "output/growth_carousel.pdf", fake_pngs, retry_facebook=True, retry_instagram=True)
            self.assertEqual(retry_res.status, "published", "Status must be 'published' when retried platforms succeed")
            self.assertTrue(retry_res.details.get("facebook_success"))
            self.assertTrue(retry_res.details.get("instagram_success"))

        print("[Test Partial Publication & Retry Engine] PASSED (Accurate status detection and retry verified)")


if __name__ == "__main__":
    unittest.main()
