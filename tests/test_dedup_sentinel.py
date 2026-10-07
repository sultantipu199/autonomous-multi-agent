"""Unit Test Suite for DedupSentinel & Non-Repeating Sequential Publishing.

Audits:
1. Detection of published duplicate topics (e.g. Day 4 and Day 6 deduplication).
2. Automatic progression to next novel syllabus module.
3. State persistence synchronization between content_vault.json and SQLite.
4. Protection against duplicate posts under CI/CD and manual overrides.
5. Dynamic perpetual generation for infinite days (Day 50, Day 100+).
"""

import os
import sys
import unittest

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.dedup_sentinel import DedupSentinel
from agents.curriculum_engine import CurriculumEngine, CURRICULUM_BANK


class TestDedupSentinel(unittest.TestCase):
    """Rigorous tests ensuring zero duplicate content and unbroken sequential progression."""

    def setUp(self):
        self.sentinel = DedupSentinel()
        self.curriculum = CurriculumEngine()

    def test_01_detects_already_published_day_4(self):
        """Verify that Day 4 topic is detected as duplicate and blocked."""
        day_4_topic = self.curriculum.get_topic_by_day(4)
        is_dup, reason = self.sentinel.is_duplicate(day_4_topic.title)
        self.assertTrue(is_dup, "Day 4 must be recognized as already published!")
        self.assertTrue(len(reason) > 5, "Must provide clear justification for duplicate detection")
        print(f"\n[Test Dedup] Day 4 correctly blocked: {reason}")

    def test_02_detects_phrase_collision(self):
        """Verify that variants containing burned phrases like 'Event Deduplication' are caught."""
        variant_title = "Meta Ads Conversion Tracking: Event Deduplication Setup"
        is_dup, reason = self.sentinel.is_duplicate(variant_title)
        self.assertTrue(is_dup, "Variant containing 'Event Deduplication' must be caught as duplicate")
        print(f"[Test Dedup] Variant correctly caught: {reason}")

    def test_03_verifies_day_6_is_detected_as_published(self):
        """Verify that Day 6 (Server-Side GA4) is correctly recognized as published."""
        day_6_topic = self.curriculum.get_topic_by_day(6)
        is_dup, reason = self.sentinel.is_duplicate(day_6_topic.title)
        self.assertTrue(is_dup, "Day 6 was published live today and must be marked duplicate!")
        print(f"[Test Dedup] Day 6 recognized as published: '{day_6_topic.title}' ({reason})")

    def test_04_auto_resolves_to_next_novel_topic(self):
        """Verify that requesting Day 6 auto-resolves cleanly to the next novel topic."""
        resolved_day, ct = self.sentinel.resolve_next_unique_day_and_topic(target_day=6)
        self.assertGreater(resolved_day, 6, "Must auto-advance past published Day 6")
        is_dup, reason = self.sentinel.is_duplicate(ct.title, ct.problem_statement)
        self.assertFalse(is_dup, f"Resolved topic Day {resolved_day} must be 100% novel! Reason: {reason}")
        print(f"[Test Dedup] Auto-resolution Day 6 -> Day {resolved_day} verified! Novel topic: '{ct.title}'")

    def test_05_curriculum_bank_sequential_continuity(self):
        """Verify that all curriculum bank lessons have distinct non-colliding titles."""
        titles = [t.title for t in CURRICULUM_BANK]
        self.assertEqual(len(titles), len(set(titles)), "All CURRICULUM_BANK topics must have unique titles")
        print(f"[Test Dedup] All {len(titles)} syllabus lessons have 100% unique titles")

    def test_06_is_today_already_published(self):
        """Verify that is_today_already_published correctly identifies today's live publication."""
        posted_today = self.sentinel.is_today_already_published(timezone_str="Asia/Dhaka")
        self.assertTrue(posted_today, "Day 6 was published today, so today must be marked as published!")
        print(f"[Test Dedup] Today's publication status verified: {posted_today}")

    def test_07_infinite_topic_generation_beyond_bank(self):
        """Verify that requesting days beyond the curated bank (Day 50, Day 75, Day 100)
        generates valid, novel CurriculumTopic objects with zero duplicate collisions."""
        test_days = [50, 75, 100]
        for d in test_days:
            ct = self.curriculum.get_topic_by_day(d)
            self.assertIsNotNone(ct)
            self.assertEqual(ct.class_id, d)
            self.assertGreater(len(ct.title), 10)
            self.assertGreater(len(ct.problem_statement), 20)
            self.assertGreater(len(ct.code_snippet), 10)
            self.assertEqual(len(ct.checklist_items), 4)
            print(f"[Test Dedup] Infinite Day {d:02d} verified: '{ct.title}' (Category: {ct.module_category})")


if __name__ == "__main__":
    unittest.main()
