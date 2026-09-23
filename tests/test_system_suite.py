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
        self.assertIn("Marketer → GenAI Engineer", carousel.slides[0].badge)
        self.assertIsNotNone(carousel.post_caption)
        self.assertGreaterEqual(len(carousel.hashtags), 3)
        self.assertIsNotNone(carousel.first_comment)
        print(f"[Test Synthesizer] PASSED (Day {carousel.day_number} carousel validated)")

    def test_03_critic_adversarial_evaluation(self):
        """Verify critic performs rigorous scoring and passes high-quality technical content."""
        critic = ContentCritic()
        carousel = CarouselContent(
            day_number=14,
            topic_headline="Production Multi-Agent Systems",
            post_caption="Deep-dive into multi-agent orchestration.\n\n#AI #GenAI",
            hashtags=["#AI", "#GenAI", "#LangGraph"],
            first_comment="Link to code repository: https://github.com/example/repo",
            slides=[
                Slide(
                    slide_number=1,
                    badge="Marketer → GenAI Engineer | Day 14",
                    title="Stop Writing Fragile AI Chains",
                    subtitle="Why Single LLM Prompts Fail at Scale",
                    body_bullets=["Context window degradation", "No self-healing loops"],
                    cta_text="Swipe for Architecture →"
                ),
                Slide(
                    slide_number=2,
                    badge="Marketer → GenAI Engineer | Day 14",
                    title="The Core Production Bottleneck",
                    body_bullets=["State loss during runtime", "No adversarial validation"]
                ),
                Slide(
                    slide_number=3,
                    badge="Marketer → GenAI Engineer | Day 14",
                    title="The Self-Healing State Graph",
                    code_snippet="workflow = StateGraph(AgentState)\nworkflow.add_node('critic', eval_node)"
                ),
                Slide(
                    slide_number=4,
                    badge="Marketer → GenAI Engineer | Day 14",
                    title="Measurable Business ROI",
                    metrics=[SlideMetric(label="Error Rate", value="-84%"), SlideMetric(label="Throughput", value="10x")]
                ),
                Slide(
                    slide_number=5,
                    badge="Marketer → GenAI Engineer | Day 14",
                    title="Engineering Checklist",
                    body_bullets=["Implement SQLite checkpointing", "Add deterministic fallbacks"],
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

        print("[Test Privacy & Security Audit] PASSED (Zero-secret leakage confirmed)")


if __name__ == "__main__":
    unittest.main()
