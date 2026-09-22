"""State definitions and Pydantic models for Autonomous Multi-Agent Growth Platform."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResearchTopic(BaseModel):
    """Scraped technical topic or discussion."""
    id: str = Field(..., description="Unique post ID (e.g. reddit_xxx or hn_xxx)")
    title: str = Field(..., description="Headline of the topic")
    url: str = Field(..., description="Source discussion URL")
    source: str = Field(..., description="Source platform (reddit/hackernews)")
    score: int = Field(default=0, description="Upvotes or score")
    num_comments: int = Field(default=0, description="Number of comments")
    summary: str = Field(default="", description="Key technical extract or summary")
    created_utc: float = Field(default=0.0, description="Timestamp of post creation")


class SlideMetric(BaseModel):
    """Key metric or ROI element displayed on a slide."""
    label: str
    value: str
    subtext: Optional[str] = None


class Slide(BaseModel):
    """Data for an individual carousel slide."""
    slide_number: int = Field(..., ge=1, le=5, description="1 to 5")
    badge: str = Field(default="Marketer → GenAI Engineer | Day 01")
    title: str = Field(..., description="Primary punchy headline")
    subtitle: Optional[str] = Field(default="", description="Secondary subtitle or context")
    body_bullets: List[str] = Field(default_factory=list, description="Bullet points or key arguments")
    code_snippet: Optional[str] = Field(default=None, description="Architecture or code breakdown")
    metrics: List[SlideMetric] = Field(default_factory=list, description="Measurable ROI or stats")
    cta_text: Optional[str] = Field(default=None, description="Action CTA (Save, Swipe, Follow)")


class CarouselContent(BaseModel):
    """Full 5-slide technical carousel package."""
    day_number: int = Field(default=1, description="Challenge/Series Day Number")
    topic_headline: str = Field(..., description="Primary topic summary")
    slides: List[Slide] = Field(..., min_length=5, max_length=5)
    post_caption: str = Field(..., description="Full LinkedIn/Meta caption with markdown & emojis")
    hashtags: List[str] = Field(default_factory=list)
    first_comment: str = Field(
        ...,
        description="First comment containing technical doc links, GitHub repo, or discussion question"
    )


class CritiqueResult(BaseModel):
    """Adversarial reflection from the Critic Agent."""
    score: float = Field(..., ge=1.0, le=10.0, description="Quality score 1.0-10.0")
    passed: bool = Field(..., description="True if score >= 8.0")
    technical_depth_score: float = Field(default=8.0)
    hook_clarity_score: float = Field(default=8.0)
    fluff_ratio_score: float = Field(default=8.0)
    feedback: str = Field(..., description="Critical evaluation feedback")
    actionable_revisions: List[str] = Field(default_factory=list)


class PublicationResult(BaseModel):
    """Publishing status across social channels."""
    linkedin_urn: Optional[str] = None
    facebook_post_id: Optional[str] = None
    instagram_container_id: Optional[str] = None
    first_comment_id: Optional[str] = None
    published_at: Optional[str] = None
    status: str = Field(default="pending")  # pending, published, skipped, failed
    mock_mode: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """Global state of the LangGraph execution pipeline."""
    topic: Optional[ResearchTopic] = None
    past_exemplars: List[Dict[str, Any]] = Field(default_factory=list)
    carousel: Optional[CarouselContent] = None
    critique: Optional[CritiqueResult] = None
    revision_count: int = 0
    human_approved: bool = False
    skipped: bool = False
    revision_request: Optional[str] = None
    rendered_images: List[str] = Field(default_factory=list)
    pdf_path: Optional[str] = None
    publication: Optional[PublicationResult] = None
    scheduled_time: Optional[str] = None
    execution_logs: List[str] = Field(default_factory=list)
