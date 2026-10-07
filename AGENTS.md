# Autonomous Multi-Agent Growth Platform (AGENTS.md)

## System Overview
Autonomous social media growth platform that operates a LangGraph multi-agent pipeline for publishing daily educational 5-slide carousels to LinkedIn, Meta Facebook Page, and Instagram Business.

## Architecture
- **Curriculum Engine (`agents/curriculum_engine.py`)**: 24-module structured digital marketing syllabus.
- **Harvester (`agents/harvester.py`)**: Gathers market insights and trending angles.
- **Synthesizer (`agents/synthesizer.py`)**: Google Gemini 3.6 Flash-powered slide copy generator.
- **Critic (`agents/critic.py`)**: Evaluates hook strength, clarity, and ROI benchmark before rendering.
- **Carousel Engine (`agents/carousel_engine.py`)**: Pillow-based 1080x1080 dark-aesthetic slide renderer and PDF compiler.
- **MultiPlatformPublisher (`agents/publisher.py`)**:
  - LinkedIn: Document post via Posts API.
  - Facebook: Multi-photo album post via Page Photos API.
  - Instagram: 100% Meta First-Party CDN-backed carousel container and publisher.
  - First Comment Engine: Delayed 120s automated technical follow-up comment.
- **Analytics Tracker (`agents/analytics_tracker.py`)**: SQLite-backed engagement tracking and memory feedback loop.
- **Orchestrator (`main.py`, `graph.py`)**: LangGraph StateGraph pipeline with Telegram Bot HITL Studio.

## Standards
- Python 3.11+
- Meta Graph API v19.0+
- First-party CDN hosting for media assets (no unreliable third-party file hosts).
