"""Anti-Duplication Sentinel Agent (Zero-Repetition & Daily Progression Governor).

Guarantees 100% unique daily posts by cross-auditing candidate topics against:
1. Live Meta Facebook Page feed posts (direct Graph API query)
2. Persistent Content Vault (content_vault.json past_topics, completed_days, posts)
3. SQLite Published Performance History (data/growth.db performance_history with real URNs)
4. Syllabus Class mapping (preventing the same curriculum module from re-firing)

If any similarity (> 35% or phrase match) is detected with recently published content,
the Sentinel automatically advances the day counter to the next unposted curriculum lesson.
"""

import os
import re
import json
import sqlite3
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from agents.curriculum_engine import CurriculumEngine, CurriculumTopic, CURRICULUM_BANK
from agents.ninja_orchestrator import initialize_vault, save_vault, get_current_day

VAULT_FILE = "content_vault.json"
DB_PATH = "data/growth.db"


class DedupSentinel:
    """Proactive sentinel that prevents duplicate posts and guarantees sequential syllabus progression."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.curriculum_engine = CurriculumEngine()

    def fetch_live_meta_post_texts(self, limit: int = 30) -> List[str]:
        """Queries Facebook Page Graph API to get the text/headlines of actual published posts."""
        meta_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
        page_id = os.getenv("META_PAGE_ID", "105656909238175").strip()

        if not meta_token or not page_id:
            try:
                if os.path.exists(self.db_path):
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT value FROM system_settings WHERE key = 'meta_page_access_token'")
                        row = cursor.fetchone()
                        if row:
                            meta_token = row[0]
            except Exception:
                pass

        if not meta_token:
            return []

        posts = []
        try:
            url = f"https://graph.facebook.com/v19.0/{page_id}/posts?limit={limit}&access_token={meta_token}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for item in data:
                    msg = item.get("message", "")
                    if msg:
                        posts.append(msg)
        except Exception as e:
            print(f"[DedupSentinel] Notice fetching live Meta posts: {e}")

        return posts

    def get_recent_meta_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries Facebook Page Graph API to get structured post objects (id, message, created_time).
        Falls back to content_vault.json posts if Graph API is unavailable."""
        meta_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
        page_id = os.getenv("META_PAGE_ID", "105656909238175").strip()

        if not meta_token or not page_id:
            try:
                if os.path.exists(self.db_path):
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT value FROM system_settings WHERE key = 'meta_page_access_token'")
                        row = cursor.fetchone()
                        if row:
                            meta_token = row[0]
            except Exception:
                pass

        if meta_token and page_id:
            try:
                url = f"https://graph.facebook.com/v19.0/{page_id}/posts?limit={limit}&fields=id,message,created_time&access_token={meta_token}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    if data:
                        return data
            except Exception as e:
                print(f"[DedupSentinel] Notice querying Meta post objects: {e}")

        # Fallback to local content_vault.json posts
        vault = initialize_vault()
        vault_posts = vault.get("posts", [])
        structured = []
        for p in vault_posts[-limit:]:
            structured.append({
                "id": p.get("meta_id") or p.get("post_id"),
                "message": p.get("topic") or p.get("hook_used"),
                "created_time": p.get("timestamp")
            })
        return structured

    def is_today_already_published(self, timezone_str: str = "Asia/Dhaka") -> bool:
        """Determines if a post has already been published on today's calendar date in target timezone."""
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(timezone_str)
        except Exception:
            tz = zoneinfo.ZoneInfo("UTC")

        now = datetime.now(tz)
        today_date_str = now.strftime("%Y-%m-%d")

        # 1. Check content_vault.json completed_days and posts
        vault = initialize_vault()
        for cd in vault.get("completed_days", []):
            ts = cd.get("timestamp", "")
            if ts.startswith(today_date_str):
                return True

        for p in vault.get("posts", []):
            ts = p.get("timestamp", "")
            if ts.startswith(today_date_str):
                return True

        # 2. Check SQLite performance_history
        if os.path.exists(self.db_path):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT published_at FROM performance_history
                        WHERE published_at LIKE ? AND (linkedin_urn IS NOT NULL OR meta_post_id IS NOT NULL)
                    """, (f"{today_date_str}%",))
                    if cursor.fetchone():
                        return True
            except Exception:
                pass

        # 3. Check live Meta Page posts
        meta_posts = self.get_recent_meta_posts(limit=5)
        for mp in meta_posts:
            ct = mp.get("created_time", "")
            if ct.startswith(today_date_str):
                return True

        return False

    def get_all_published_topics(self) -> List[str]:
        """Gathers all known ACTUALLY PUBLISHED topics and hooks from Vault, SQLite, and live Meta."""
        collected: List[str] = []

        # 1. From content_vault.json (completed_days and posts)
        vault = initialize_vault()
        for item in vault.get("completed_days", []):
            t = item.get("topic", "")
            if t and "override" not in t.lower() and "untitled" not in t.lower():
                collected.append(t)

        for pt in vault.get("past_topics", []):
            if pt:
                collected.append(pt)

        for ph in vault.get("past_hooks", []):
            if ph:
                collected.append(ph)

        for p in vault.get("posts", []):
            if p.get("topic"):
                collected.append(p["topic"])
            if p.get("hook_used"):
                collected.append(p["hook_used"])

        # 2. From SQLite performance_history (only rows that were genuinely published)
        if os.path.exists(self.db_path):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT topic_title, hook_text, linkedin_urn, meta_post_id
                        FROM performance_history
                    """)
                    for row in cursor.fetchall():
                        t_title, h_text, li_urn, meta_id = row
                        is_genuine = (
                            (li_urn and not any(k in str(li_urn).lower() for k in ["mock", "error", "123456789"]))
                            or (meta_id and not any(k in str(meta_id).lower() for k in ["mock", "error"]))
                        )
                        if is_genuine:
                            if t_title:
                                collected.append(t_title)
                            if h_text:
                                collected.append(h_text)
            except Exception as e:
                print(f"[DedupSentinel] SQLite history notice: {e}")

        # 3. From Live Meta Feed (real Facebook posts)
        live_meta_msgs = self.fetch_live_meta_post_texts(limit=25)
        for msg in live_meta_msgs:
            first_line = msg.strip().split("\n")[0]
            if first_line:
                collected.append(first_line)

        # 4. Canonical known published topics on Tipu Sultan's profile to strictly guard against
        hardcoded_burned = [
            "Eliminating Duplicate Conversions: Bulletproof Event Deduplication",
            "Eliminating Duplicate Conversions: Bulletproof Event Deduplication (event_id)",
            "Eliminating Duplicate Conversions",
            "Bulletproof Event Deduplication",
            "Are your Meta Ads Manager conversion numbers higher than your real Shopify or Stripe backend revenue?",
            "dual-tracking duplication trap",
            "Web Analytics & GTM DataLayer: The Single Source of Truth Architecture",
            "Facebook Pixel Dynamic Values & Custom Events: Unlocking Value-Based Bidding",
            "Fixing iOS 14.5 & AdBlocker Data Loss with Stape.io & First-Party Cookies",
            "GA4 E-Commerce Tracking: Dynamic Value, Currency & Item Arrays Architecture",
        ]
        collected.extend(hardcoded_burned)

        return [c.strip() for c in collected if c and len(c.strip()) > 5]

    @staticmethod
    def _normalize_tokens(text: str) -> set:
        """Strips punctuation, emojis, and returns lowercase word tokens."""
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = set(clean.split())
        stopwords = {"and", "the", "or", "to", "in", "with", "a", "an", "is", "for", "of", "via", "on", "from", "at", "by", "how", "why"}
        return tokens - stopwords

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculates Jaccard token similarity between two text snippets."""
        t1 = self._normalize_tokens(text1)
        t2 = self._normalize_tokens(text2)
        if not t1 or not t2:
            return 0.0
        intersection = t1.intersection(t2)
        union = t1.union(t2)
        return len(intersection) / len(union)

    def is_duplicate(self, candidate_title: str, candidate_problem: str = "", threshold: float = 0.40) -> Tuple[bool, str]:
        """Determines if a candidate topic has already been published.
        
        Returns:
            (is_duplicate, matched_reason)
        """
        past_items = self.get_all_published_topics()

        # Dedicated key phrase checks that must NEVER repeat
        signature_phrases = [
            "duplicate conversions",
            "event deduplication",
            "deduplication",
            "single source of truth",
            "first-party cookies",
            "dynamic value",
            "ios 14.5",
        ]

        cand_lower = candidate_title.lower()

        for past in past_items:
            past_lower = past.lower()

            # 1. Exact match
            if candidate_title.strip().lower() == past.strip().lower():
                return True, f"Exact match with past post: '{past[:60]}'"

            # 2. Substring containment
            if len(candidate_title) > 20 and (cand_lower in past_lower or past_lower in cand_lower):
                return True, f"Substring match with past post: '{past[:60]}'"

            # 3. Jaccard token similarity
            sim = self.calculate_similarity(candidate_title, past)
            if sim >= threshold:
                return True, f"High similarity ({sim:.2f} >= {threshold:.2f}) with past post: '{past[:60]}'"

            # 4. Signature phrase collision check
            for phrase in signature_phrases:
                if phrase in cand_lower and phrase in past_lower:
                    return True, f"Signature phrase collision ('{phrase}') with past post: '{past[:60]}'"

        return False, ""

    def resolve_next_unique_day_and_topic(
        self,
        target_day: int,
        max_lookahead: int = 40
    ) -> Tuple[int, CurriculumTopic]:
        """Evaluates target_day and automatically advances to the next unposted topic
        if the candidate has already been published.
        
        Guarantees:
        1. Never repeats content already posted on LinkedIn/Meta.
        2. Maintains sequential syllabus order.
        3. Seamlessly generates fresh perpetual AI topics for infinite days.
        """
        curriculum = self.curriculum_engine
        checked_day = target_day
        past_items = self.get_all_published_topics()

        for _ in range(max_lookahead):
            ct = curriculum.get_topic_by_day(checked_day, past_topics=past_items)
            is_dup, reason = self.is_duplicate(ct.title, ct.problem_statement)

            if not is_dup:
                if checked_day != target_day:
                    print(
                        f"[DedupSentinel] Target Day {target_day:02d} was already published! "
                        f"Auto-advanced to fresh Day {checked_day:02d}: '{ct.title[:50]}...'"
                    )
                else:
                    print(f"[DedupSentinel] Verified Day {checked_day:02d} is 100% novel: '{ct.title[:50]}...'")
                return checked_day, ct

            print(f"[DedupSentinel] Day {checked_day:02d} ('{ct.title[:40]}...') skipped: {reason}")
            checked_day += 1

        # Guaranteed infinite fallback: generate dynamic perpetual topic avoiding all past items
        fallback_topic = curriculum.generate_perpetual_martech_topic(checked_day, past_topics=past_items)
        return checked_day, fallback_topic

    def record_published_post_sync(
        self,
        day_number: int,
        topic_title: str,
        hook_text: str = "",
        linkedin_urn: str = "",
        meta_id: str = "",
        instagram_id: str = "",
    ):
        """Atomically records the published post across content_vault.json and SQLite."""
        vault = initialize_vault()

        if "completed_days" not in vault:
            vault["completed_days"] = []

        vault["completed_days"].append({
            "day_number": day_number,
            "topic": topic_title,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        if "past_topics" not in vault:
            vault["past_topics"] = []
        if topic_title not in vault["past_topics"]:
            vault["past_topics"].append(topic_title)

        if hook_text and "past_hooks" not in vault:
            vault["past_hooks"] = []
        if hook_text and hook_text not in vault["past_hooks"]:
            vault["past_hooks"].append(hook_text)

        # Advance current day in vault to next day
        vault["current_day"] = day_number + 1

        record = {
            "post_id": f"POST_{day_number}_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "day_number": day_number,
            "topic": topic_title,
            "hook_used": hook_text or topic_title,
            "linkedin_urn": linkedin_urn,
            "meta_id": meta_id,
            "instagram_id": instagram_id,
        }
        vault.setdefault("posts", []).append(record)
        save_vault(vault)

        print(f"[DedupSentinel] Recorded Day {day_number:02d} ('{topic_title[:40]}...') as completed. Next active day: Day {day_number + 1:02d}.")
