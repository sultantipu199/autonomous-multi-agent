"""Harvester Agent: Scrapes trending tech discussions from Reddit and Hacker News

Includes 30-day SQLite novelty deduplication to ensure content freshness and prevent repeating topics.
"""

import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from state import ResearchTopic
from agents.curriculum_engine import CurriculumEngine


class ContentHarvester:
    """Harvests authoritative syllabus topics and trending digital marketing & tracking insights."""

    def __init__(self, db_path: str = "data/growth.db"):
        self.db_path = db_path
        self.curriculum_engine = CurriculumEngine()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initializes SQLite schema for deduplication."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS harvested_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT,
                    source TEXT,
                    score INTEGER,
                    num_comments INTEGER,
                    harvested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_novel(self, item_id: str, days_window: int = 30) -> bool:
        """Checks if an item was harvested in the past N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_window)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM harvested_items WHERE id = ? AND harvested_at >= ?",
                (item_id, cutoff.isoformat())
            )
            return cursor.fetchone() is None

    def mark_harvested(self, item: ResearchTopic):
        """Records a harvested item into SQLite for future deduplication."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO harvested_items (id, title, url, source, score, num_comments, harvested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.title,
                    item.url,
                    item.source,
                    item.score,
                    item.num_comments,
                    datetime.now(timezone.utc).isoformat(),
                )
            )
            conn.commit()

    def fetch_reddit(self, subreddits: List[str] = None) -> List[ResearchTopic]:
        """Fetches top technical posts from Reddit subreddits concurrently."""
        if subreddits is None:
            subreddits = ["MachineLearning", "LocalLLaMA", "ArtificialIntelligence"]

        results = []
        headers = {"User-Agent": "AutonomousMultiAgentPlatform/1.0 (GrowthEngine; by GenAIEngineer)"}

        def _fetch_sub(sub: str) -> List[ResearchTopic]:
            sub_results = []
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
            try:
                resp = requests.get(url, headers=headers, timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post = child.get("data", {})
                        post_id = f"reddit_{post.get('id')}"
                        title = post.get("title", "").strip()
                        permalink = f"https://reddit.com{post.get('permalink', '')}"
                        score = post.get("score", 0)
                        comments = post.get("num_comments", 0)
                        selftext = post.get("selftext", "")[:400]

                        # Quality filter: skip sticky or ultra-low score
                        if post.get("stickied") or score < 10:
                            continue

                        sub_results.append(
                            ResearchTopic(
                                id=post_id,
                                title=title,
                                url=permalink,
                                source=f"reddit/r/{sub}",
                                score=score,
                                num_comments=comments,
                                summary=selftext or f"Trending discussion on r/{sub} with {score} upvotes.",
                                created_utc=post.get("created_utc", 0.0),
                            )
                        )
            except Exception:
                pass
            return sub_results

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_fetch_sub, sub) for sub in subreddits]
            for future in as_completed(futures):
                try:
                    results.extend(future.result())
                except Exception:
                    pass

        return results

    def fetch_hacker_news(self, limit: int = 15) -> List[ResearchTopic]:
        """Fetches top technical discussions from Hacker News concurrently."""
        results = []
        try:
            top_ids_resp = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=3
            )
            if top_ids_resp.status_code != 200:
                return results

            top_ids = top_ids_resp.json()[:limit]

            def _fetch_item(story_id: int) -> Optional[ResearchTopic]:
                try:
                    item_resp = requests.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                        timeout=3,
                    )
                    if item_resp.status_code == 200:
                        item = item_resp.json()
                        title = item.get("title", "")
                        score = item.get("score", 0)
                        comments = len(item.get("kids", []))
                        url = item.get("url") or f"https://news.ycombinator.com/item?id={story_id}"

                        ai_keywords = ["ai", "llm", "agent", "model", "langchain", "gpu", "inference", "rag", "code", "latency", "system", "graph"]
                        if any(k in title.lower() for k in ai_keywords) or score > 100:
                            return ResearchTopic(
                                id=f"hn_{story_id}",
                                title=title,
                                url=url,
                                source="hackernews",
                                score=score,
                                num_comments=comments,
                                summary=f"Hacker News top story with {score} points and {comments} comments.",
                                created_utc=item.get("time", 0.0),
                            )
                except Exception:
                    pass
                return None

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(_fetch_item, sid) for sid in top_ids]
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        if res:
                            results.append(res)
                    except Exception:
                        pass

        except Exception:
            pass

        return results

    def get_fallback_topics(self) -> List[ResearchTopic]:
        """Curated high-signal fallback topics for sandbox mode or offline execution."""
        return [
            ResearchTopic(
                id="fallback_langgraph_memory",
                title="LangGraph v0.2 Checkpointing with SQLite: Solving Production Multi-Turn Latency",
                url="https://github.com/langchain-ai/langgraph",
                source="engineering_curated",
                score=342,
                num_comments=89,
                summary="Deep dive into StateGraph SQLite disk checkpointing, human-in-the-loop pause/resume mechanics, and sub-second agent state persistence.",
                created_utc=time.time(),
            ),
            ResearchTopic(
                id="fallback_agentic_rag_routing",
                title="Adaptive RAG with Dynamic Query Decomposition & Self-Correction Loops",
                url="https://arxiv.org/abs/2401.15884",
                source="arxiv_curated",
                score=512,
                num_comments=120,
                summary="Benchmarking semantic routing vs agentic re-ranking. How self-correction cut false retrieval hallucination by 74% in production pipelines.",
                created_utc=time.time(),
            ),
            ResearchTopic(
                id="fallback_vllm_batching_optimization",
                title="Cutting Enterprise LLM Serving Costs by 65% with Continuous Batching & PagedAttention",
                url="https://github.com/vllm-project/vllm",
                source="systems_curated",
                score=430,
                num_comments=75,
                summary="Architecture breakdown of memory fragmentation reduction in GPU vRAM using PagedAttention, increasing token throughput by 4.2x.",
                created_utc=time.time(),
            ),
        ]

    def harvest_best_topic(self, day_number: int = 1) -> ResearchTopic:
        """Selects authoritative syllabus topic for the day, strictly anchored in the Master Curriculum."""
        # 1. Primary Root Source: Master Digital Marketing & Server-Side Tracking Syllabus
        syllabus_topic = self.curriculum_engine.get_as_research_topic(day_number)
        
        if self.is_novel(syllabus_topic.id, days_window=60):
            self.mark_harvested(syllabus_topic)
            return syllabus_topic

        # Rotate through syllabus topics
        candidates: List[ResearchTopic] = [syllabus_topic]
        for offset in range(1, 15):
            alt_topic = self.curriculum_engine.get_as_research_topic(day_number + offset)
            if self.is_novel(alt_topic.id, days_window=60):
                self.mark_harvested(alt_topic)
                return alt_topic
            candidates.append(alt_topic)

        # Fallback if entire rotation cycle has been seen
        selected = candidates[0]
        self.mark_harvested(selected)
        return selected
