"""Analytics Tracker & Reinforcement Learning from Social Feedback (RLSF).

Tracks reactions, comments, and shares across LinkedIn and Meta APIs over a rolling 7-day window.
Calculates weighted engagement scores, stores them in SQLite, and provides top-performing
exemplars to the Synthesizer for continuous reach optimization.
"""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import requests


class AnalyticsTracker:
    """Manages social metrics retrieval, scoring, and few-shot memory feedback."""

    def __init__(self, db_path: str = "data/growth.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._seed_baseline_if_empty()

    def _init_db(self):
        """Initializes performance history table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id TEXT,
                    topic_title TEXT NOT NULL,
                    hook_text TEXT,
                    linkedin_urn TEXT,
                    meta_post_id TEXT,
                    reactions INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0.0,
                    post_format TEXT DEFAULT 'carousel_pdf',
                    code_snippet_included INTEGER DEFAULT 1,
                    published_at TIMESTAMP,
                    last_synced_at TIMESTAMP
                )
            """)
            conn.commit()

    def _seed_baseline_if_empty(self):
        """Seeds high-performing baseline exemplars if performance history is empty."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM performance_history")
            count = cursor.fetchone()[0]
            if count == 0:
                baselines = [
                    (
                        "seed_01",
                        "Building Async AI Agents with LangGraph & SQLite Checkpoints",
                        "Most engineers use basic in-memory LLM chains. Here is why enterprise systems crash without disk checkpointing.",
                        "urn:li:share:seed_101",
                        "meta_seed_101",
                        284,
                        47,
                        29,
                        517.5,
                        "carousel_pdf",
                        1,
                        (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                    (
                        "seed_02",
                        "Bridging Marketing & GenAI: How We Cut Lead Triage Costs by 82%",
                        "Why our agency fired manual lead scoring and built an autonomous LangGraph evaluator that runs on $0.003/query.",
                        "urn:li:share:seed_102",
                        "meta_seed_102",
                        315,
                        58,
                        34,
                        596.0,
                        "carousel_pdf",
                        1,
                        (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                    (
                        "seed_03",
                        "Why 90% of RAG Systems Fail in Production (And the 3 Fixes)",
                        "Vector similarity search is not enough. Here is the hybrid BM25 + Cross-Encoder re-ranking architecture that actually works.",
                        "urn:li:share:seed_103",
                        "meta_seed_103",
                        410,
                        82,
                        53,
                        827.0,
                        "carousel_pdf",
                        1,
                        (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                ]
                cursor.executemany("""
                    INSERT INTO performance_history (
                        topic_id, topic_title, hook_text, linkedin_urn, meta_post_id,
                        reactions, comments, shares, engagement_score, post_format,
                        code_snippet_included, published_at, last_synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, baselines)
                conn.commit()

    def record_published_post(
        self,
        topic_id: str,
        topic_title: str,
        hook_text: str,
        linkedin_urn: Optional[str] = None,
        meta_post_id: Optional[str] = None,
        code_snippet_included: bool = True,
    ):
        """Records a freshly published post for upcoming 7-day tracking."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_history (
                    topic_id, topic_title, hook_text, linkedin_urn, meta_post_id,
                    reactions, comments, shares, engagement_score, post_format,
                    code_snippet_included, published_at, last_synced_at
                ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0.0, 'carousel_pdf', ?, ?, ?)
            """, (
                topic_id,
                topic_title,
                hook_text,
                linkedin_urn,
                meta_post_id,
                1 if code_snippet_included else 0,
                now,
                now,
            ))
            conn.commit()

    def calculate_engagement_score(self, reactions: int, comments: int, shares: int) -> float:
        """Weighted engagement score prioritizing active conversation and distribution:

        Reactions = 1.0x, Comments = 2.5x, Shares/Reposts = 4.0x
        """
        return (reactions * 1.0) + (comments * 2.5) + (shares * 4.0)

    def sync_recent_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Syncs social metrics from LinkedIn & Meta APIs for the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        meta_token = os.getenv("META_PAGE_ACCESS_TOKEN")
        mock_mode = os.getenv("MOCK_MODE", "True").lower() == "true"

        posts_to_sync = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, linkedin_urn, meta_post_id, topic_title, reactions, comments, shares
                FROM performance_history
                WHERE published_at >= ?
            """, (cutoff,))
            posts_to_sync = cursor.fetchall()

        synced_count = 0
        now_str = datetime.now(timezone.utc).isoformat()

        for post_id, li_urn, meta_id, title, prev_r, prev_c, prev_s in posts_to_sync:
            reactions, comments, shares = prev_r, prev_c, prev_s

            if not mock_mode and linkedin_token and li_urn:
                try:
                    # LinkedIn Organizational/Community Analytics API call
                    url = f"https://api.linkedin.com/v2/organizationalEntityShareStatistics?q=organizationalEntity&shares[0]={li_urn}"
                    headers = {"Authorization": f"Bearer {linkedin_token}"}
                    r = requests.get(url, headers=headers, timeout=5)
                    if r.status_code == 200:
                        elements = r.json().get("elements", [])
                        if elements:
                            stats = elements[0].get("totalShareStatistics", {})
                            reactions = stats.get("likeCount", reactions)
                            comments = stats.get("commentCount", comments)
                            shares = stats.get("shareCount", shares)
                except Exception:
                    pass

            if not mock_mode and meta_token and meta_id:
                try:
                    # Meta Graph API post insights
                    url = f"https://graph.facebook.com/v19.0/{meta_id}?fields=reactions.summary(total_count),comments.summary(total_count),shares&access_token={meta_token}"
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        meta_reactions = data.get("reactions", {}).get("summary", {}).get("total_count", 0)
                        meta_comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
                        meta_shares = data.get("shares", {}).get("count", 0)
                        reactions += meta_reactions
                        comments += meta_comments
                        shares += meta_shares
                except Exception:
                    pass

            # In sandbox / mock mode, simulate realistic organic engagement growth
            if mock_mode and (reactions == 0 and comments == 0 and shares == 0):
                import random
                reactions = random.randint(45, 180)
                comments = random.randint(8, 35)
                shares = random.randint(4, 18)

            score = self.calculate_engagement_score(reactions, comments, shares)

            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE performance_history
                    SET reactions = ?, comments = ?, shares = ?, engagement_score = ?, last_synced_at = ?
                    WHERE id = ?
                """, (reactions, comments, shares, score, now_str, post_id))
                conn.commit()

            synced_count += 1

        return {
            "synced_posts_count": synced_count,
            "window_days": days,
            "timestamp": now_str,
        }

    def get_top_exemplars(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Extracts top-performing topics and formats to inject as few-shot guidance into Gemini Pro."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT topic_title, hook_text, engagement_score, reactions, comments, shares
                FROM performance_history
                WHERE engagement_score > 0
                ORDER BY engagement_score DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
