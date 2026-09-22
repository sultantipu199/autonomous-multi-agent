"""LangGraph State Machine with SqliteSaver disk checkpointing and HITL interruption.

Orchestrates the entire growth workflow: Dynamic Scheduling -> Novelty Harvester ->
RLSF Memory -> Synthesizer -> Adversarial Critic -> 5-Slide Visual Engine ->
Human-In-The-Loop Review -> Multi-Platform Publisher + First Comment.
"""

import os
import sqlite3
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from state import ResearchTopic, CarouselContent, CritiqueResult, PublicationResult
from agents.dynamic_scheduler import get_dynamic_schedule
from agents.harvester import ContentHarvester
from agents.analytics_tracker import AnalyticsTracker
from agents.synthesizer import ContentSynthesizer
from agents.critic import ContentCritic
from agents.carousel_engine import CarouselEngine
from agents.publisher import MultiPlatformPublisher

load_dotenv()


class PipelineState(TypedDict):
    """LangGraph compatible State Schema for serialization and disk persistence."""
    day_number: int
    scheduled_slot: Optional[Dict[str, Any]]
    topic: Optional[Dict[str, Any]]
    past_exemplars: List[Dict[str, Any]]
    carousel: Optional[Dict[str, Any]]
    critique: Optional[Dict[str, Any]]
    revision_count: int
    revision_request: Optional[str]
    rendered_images: List[str]
    pdf_path: Optional[str]
    human_approved: bool
    skipped: bool
    publication: Optional[Dict[str, Any]]
    logs: List[str]


# ------------------------------------------------------------------------------
# Graph Nodes
# ------------------------------------------------------------------------------

def schedule_node(state: PipelineState) -> Dict[str, Any]:
    """Calculates peak publication window with organic jitter."""
    slot = get_dynamic_schedule()
    log_msg = f"[DynamicScheduler] Calculated target slot: {slot.get('scheduled_time_display')} (Jitter: {slot.get('micro_jitter_seconds')}s)"
    print(log_msg)
    return {
        "scheduled_slot": slot,
        "logs": state.get("logs", []) + [log_msg]
    }


def memory_node(state: PipelineState) -> Dict[str, Any]:
    """Syncs social analytics from past 7 days and extracts top exemplars."""
    tracker = AnalyticsTracker()
    sync_stats = tracker.sync_recent_analytics(days=7)
    exemplars = tracker.get_top_exemplars(limit=3)
    log_msg = f"[Memory] Synced {sync_stats.get('synced_posts_count')} posts. Retrieved {len(exemplars)} top RLSF exemplars."
    print(log_msg)
    return {
        "past_exemplars": exemplars,
        "logs": state.get("logs", []) + [log_msg]
    }


def harvester_node(state: PipelineState) -> Dict[str, Any]:
    """Scrapes trending topics from Reddit & Hacker News with 30-day SQLite deduplication."""
    harvester = ContentHarvester()
    selected_topic: ResearchTopic = harvester.harvest_best_topic()
    log_msg = f"[Harvester] Selected novel topic: '{selected_topic.title}' (Source: {selected_topic.source}, Score: {selected_topic.score})"
    print(log_msg)
    return {
        "topic": selected_topic.model_dump(),
        "logs": state.get("logs", []) + [log_msg]
    }


def synthesizer_node(state: PipelineState) -> Dict[str, Any]:
    """Generates the 5-slide technical carousel package with persona & exemplar conditioning."""
    synthesizer = ContentSynthesizer()
    topic_data = state.get("topic") or {}
    topic = ResearchTopic.model_validate(topic_data)
    exemplars = state.get("past_exemplars", [])
    day_number = state.get("day_number", 14)
    revision_req = state.get("revision_request")
    existing_carousel = CarouselContent.model_validate(state["carousel"]) if state.get("carousel") else None

    carousel: CarouselContent = synthesizer.synthesize_carousel(
        topic=topic,
        exemplars=exemplars,
        day_number=day_number,
        revision_request=revision_req,
        existing_carousel=existing_carousel,
    )

    rev_count = state.get("revision_count", 0)
    log_msg = f"[Synthesizer] Generated 5 slides for Day {day_number}. (Revision iteration: {rev_count})"
    print(log_msg)

    return {
        "carousel": carousel.model_dump(),
        "revision_count": rev_count + 1 if revision_req else rev_count,
        "revision_request": None,  # Reset request once consumed
        "logs": state.get("logs", []) + [log_msg]
    }


def critic_node(state: PipelineState) -> Dict[str, Any]:
    """Adversarially evaluates technical depth, fluff ratio, and persona consistency."""
    critic = ContentCritic()
    carousel = CarouselContent.model_validate(state["carousel"])
    critique: CritiqueResult = critic.evaluate(carousel)

    log_msg = f"[Critic] Score: {critique.score}/10 (Passed: {critique.passed}). Feedback: {critique.feedback}"
    print(log_msg)

    return {
        "critique": critique.model_dump(),
        "logs": state.get("logs", []) + [log_msg]
    }


def route_after_critic(state: PipelineState) -> str:
    """Routes back to synthesizer if critic fails and revision limit not reached."""
    critique = state.get("critique", {})
    passed = critique.get("passed", False)
    rev_count = state.get("revision_count", 0)

    if not passed and rev_count < 2:
        print(f"[Router] Critic score under 8.0. Routing back to synthesizer for revision {rev_count + 1}...")
        return "synthesizer"
    return "render_carousel"


def render_carousel_node(state: PipelineState) -> Dict[str, Any]:
    """Renders 5 dark-theme aesthetic slides (1080x1080) and compiles growth_carousel.pdf."""
    engine = CarouselEngine()
    carousel = CarouselContent.model_validate(state["carousel"])
    png_paths, pdf_path = engine.render_all(carousel)

    log_msg = f"[CarouselEngine] Rendered {len(png_paths)} slides (1080x1080) and compiled PDF: {pdf_path}"
    print(log_msg)

    return {
        "rendered_images": png_paths,
        "pdf_path": pdf_path,
        "logs": state.get("logs", []) + [log_msg]
    }


def human_review_node(state: PipelineState) -> Dict[str, Any]:
    """Human-in-the-loop review node. Execution pauses here until approved or revised."""
    log_msg = f"[HITL] Human review reached. Approval status: {state.get('human_approved')}, Skipped: {state.get('skipped')}"
    print(log_msg)
    return {
        "logs": state.get("logs", []) + [log_msg]
    }


def route_after_human(state: PipelineState) -> str:
    """Determines whether to publish, re-synthesize revision, or terminate if skipped."""
    if state.get("skipped"):
        print("[Router] Post skipped by user. Exiting.")
        return END
    if state.get("revision_request"):
        print(f"[Router] Human requested revision: '{state.get('revision_request')}'. Routing to synthesizer.")
        return "synthesizer"
    if state.get("human_approved"):
        print("[Router] Human approved draft. Proceeding to publication.")
        return "publish"
    return END


def publish_node(state: PipelineState) -> Dict[str, Any]:
    """Dispatches carousel to LinkedIn, Meta, Instagram and injects First Comment."""
    publisher = MultiPlatformPublisher()
    carousel = CarouselContent.model_validate(state["carousel"])
    pdf_path = state.get("pdf_path", "output/growth_carousel.pdf")
    png_paths = state.get("rendered_images", [])

    result: PublicationResult = publisher.publish_all(
        carousel=carousel,
        pdf_path=pdf_path,
        png_paths=png_paths,
        async_first_comment=True,
    )

    log_msg = f"[Publisher] Published with status '{result.status}'. LinkedIn URN: {result.linkedin_urn}"
    print(log_msg)

    return {
        "publication": result.model_dump(),
        "logs": state.get("logs", []) + [log_msg]
    }


# ------------------------------------------------------------------------------
# Graph Construction & Compilation
# ------------------------------------------------------------------------------

def build_growth_graph(checkpoint_db_path: str = "data/checkpoints.db", enable_interrupt: bool = True):
    """Builds and compiles the StateGraph workflow with persistent SqliteSaver checkpointing."""
    os.makedirs(os.path.dirname(checkpoint_db_path), exist_ok=True)
    conn = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    builder = StateGraph(PipelineState)

    # Register Nodes
    builder.add_node("schedule", schedule_node)
    builder.add_node("memory", memory_node)
    builder.add_node("harvester", harvester_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("critic", critic_node)
    builder.add_node("render_carousel", render_carousel_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("publish", publish_node)

    # Add Edges
    builder.add_edge(START, "schedule")
    builder.add_edge("schedule", "memory")
    builder.add_edge("memory", "harvester")
    builder.add_edge("harvester", "synthesizer")
    builder.add_edge("synthesizer", "critic")

    # Conditional edge: Critic evaluation loop
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "synthesizer": "synthesizer",
            "render_carousel": "render_carousel"
        }
    )

    builder.add_edge("render_carousel", "human_review")

    # Conditional edge: Human decision (Approve / Revise / Skip)
    builder.add_conditional_edges(
        "human_review",
        route_after_human,
        {
            "publish": "publish",
            "synthesizer": "synthesizer",
            END: END
        }
    )

    builder.add_edge("publish", END)

    # Interrupt before human_review for Telegram Studio approval if requested
    interrupt_nodes = ["human_review"] if enable_interrupt else []

    app = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_nodes
    )
    return app
