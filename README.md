# Autonomous Multi-Agent Growth Platform (Agency Grade)

A production-grade, self-learning autonomous social growth engine architected with **LangGraph v0.2+**, featuring algorithmic dynamic scheduling, SQLite-backed reinforcement learning from social engagement, Pillow-powered 1080x1080 dark-theme carousel generation, PyMuPDF/Pillow PDF compilation, automated first-comment injection, and human-in-the-loop (HITL) Telegram Studio approval with multi-turn revisions.

---

## Architecture Diagram

```
+---------------------------------------------------------------------------------+
|                         DYNAMIC SCHEDULER & RLSF MEMORY                         |
|   - 08:30 - 11:30 BD Time Peak Window + Organic Jitter (randomized micro-shifts) |
|   - Past 7-Day Social Metrics Tracked via LinkedIn Analytics & Meta Graph APIs   |
|   - Top-Performing Exemplars injected as few-shot memory into Gemini Pro        |
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                           CONTENT HARVESTER & SYNTHESIS                         |
|   - Scrapes Reddit (r/MachineLearning, r/LocalLLaMA) & Hacker News              |
|   - 30-Day SQLite Novelty Deduplication (`data/growth.db`)                      |
|   - Synthesizer (Gemini Pro / Flash) produces "Marketer → GenAI Engineer" persona|
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                       ADVERSARIAL CRITIC (QUALITY GATE)                         |
|   - Evaluates technical depth, fluff ratio, code quality, and persona standards  |
|   - Auto-loops back for revision if score < 8.0/10                              |
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                   CAROUSEL & PDF RENDERING ENGINE (1080x1080)                   |
|   - Dark theme `#0D1117`, syntax-highlighted code terminals, ROI metric cards   |
|   - Slide 1: High-Contrast Hook + Author Brand Badge                            |
|   - Slide 2: Core Engineering Problem / Live Tech Trend                         |
|   - Slide 3: Architecture Diagram / Code Snippet breakdown                     |
|   - Slide 4: Business Value & Measurable ROI (Tech & Marketing)                 |
|   - Slide 5: Summary Checklist + "Swipe/Save for Later" CTA                     |
|   - Compiles slides into `output/growth_carousel.pdf`                           |
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                     INTERACTIVE TELEGRAM STUDIO (LANGGRAPH HITL)                |
|   - SqliteSaver disk checkpointing (`data/checkpoints.db`)                      |
|   - Delivers 5 images (MediaGroup) + PDF document + full formatted post caption |
|   - Inline buttons: [🚀 Approve & Post All] | [✏️ Interactive Revision] | [⏭️ Skip] |
|   - Supports natural language revisions (e.g. Bengali/English revision prompts) |
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                   MULTI-PLATFORM PUBLISHER & FIRST-COMMENT ENGINE               |
|   - LinkedIn Document Post API (PDF carousel)                                   |
|   - Meta Facebook Page API & Instagram Carousel Container API                   |
|   - Automated First-Comment: Drops technical docs/GitHub link 120s post-publish |
+---------------------------------------------------------------------------------+
```

---

## File Structure

```
├── .github/workflows/
│   └── daily_growth.yml         # GitHub Actions daily cron pipeline (03:00 UTC / 09:00 BD)
├── agents/
│   ├── __init__.py
│   ├── analytics_tracker.py     # 7-day social metrics tracking & RLSF SQLite memory loop
│   ├── carousel_engine.py       # Pillow 1080x1080 dark-theme renderer + PDF compiler
│   ├── critic.py                # Adversarial self-reflection quality scoring
│   ├── dynamic_scheduler.py     # Peak BD Time window calculator with organic jitter
│   ├── harvester.py             # Reddit & Hacker News scraper with 30-day deduplication
│   ├── publisher.py             # Multi-platform distributor + 120s first-comment injector
│   └── synthesizer.py           # Gemini Pro content generator with exemplar injection
├── data/
│   ├── growth.db                # SQLite database (harvested items & performance history)
│   └── checkpoints.db           # LangGraph SqliteSaver disk checkpoints
├── output/
│   ├── slide_1.png ... slide_5.png # 1080x1080 high-retention slides
│   └── growth_carousel.pdf     # Compiled PDF document for LinkedIn
├── .env.example                 # Configuration template
├── graph.py                     # LangGraph StateGraph pipeline definition
├── main.py                      # Telegram Studio Bot & CLI runner
├── requirements.txt             # Production dependencies
└── state.py                     # Pydantic data schemas
```

---

## Quick Start

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and configure your credentials:
```bash
cp .env.example .env
```

Key configuration options:
- `MOCK_MODE`: Set to `True` to run completely in sandbox mode without live social API keys.
- `GEMINI_API_KEY`: Your Google Gemini API key.
- `TELEGRAM_BOT_TOKEN`: Your bot token from `@BotFather`.
- `TELEGRAM_CHAT_ID`: Your target chat ID.
- `LINKEDIN_ACCESS_TOKEN` & `LINKEDIN_AUTHOR_URN`: LinkedIn posting credentials.
- `META_PAGE_ACCESS_TOKEN` & `META_PAGE_ID`: Facebook Page posting credentials.
- `INSTAGRAM_ACCOUNT_ID`: Instagram Business Account ID.

---

## Execution Modes

### Mode 1: Interactive Telegram Studio (Production HITL)
Start the Telegram Studio bot:
```bash
python main.py
```
Open Telegram and message your bot:
- `/generate`: Triggers research, renders the 5 slides, compiles the PDF, and presents preview buttons:
  - `[🚀 Approve & Post All]`: Publishes to LinkedIn, Meta, and Instagram, and schedules the 120-second first comment.
  - `[✏️ Interactive Revision]`: Prompts you for plain text revisions (e.g. *"Slide 3-এর কোড স্নিপেটে LangGraph latency উল্লেখ করো"*), triggering a targeted re-render.
  - `[⏭️ Skip Today]`: Aborts the post and checkpoints state.
- `/status`: Displays current scheduling slot and performance memory.

### Mode 2: Headless CLI Mode (Testing & Verification)
Run the pipeline directly in your terminal:
```bash
python main.py --cli
```

Auto-approve mode (publishes without manual review):
```bash
python main.py --cli --auto-approve
```

Test natural language revision re-rendering via CLI:
```bash
python main.py --cli --revision "Slide 3-এর কোড স্নিপেটে LangGraph latency উল্লেখ করো"
```

---

## Features Breakdown

### 1. Self-Balancing Dynamic Schedule (Algorithmic Timing)
- Avoids rigid mechanical bot timing.
- Calculates an adaptive window between **08:30 AM and 11:30 AM BD Time** (Asia/Dhaka / UTC+6).
- Injects organic micro-jitter to simulate genuine human publication habits.

### 2. Post-Publish Analytics & RLSF Self-Learning Memory
- Scrapes engagement metrics (reactions, comments, shares) of the previous 7 days' posts.
- Weighted engagement score formula: `(reactions * 1.0) + (comments * 2.5) + (shares * 4.0)`.
- Automatically injects top-performing topics and structures as few-shot exemplars into Gemini Pro.

### 3. High-Retention 5-Slide Visual Carousel (Pillow + PyMuPDF)
- Native 1080x1080 dark aesthetic `#0D1117` GitHub dark theme.
- Slide 1: High-contrast Hook + Author Brand Badge (`Marketer → GenAI Engineer | Day [N]`).
- Slide 2: Core Engineering Problem / Live Tech Trend.
- Slide 3: Architecture Diagram / Code Snippet with Mac-style window controls and syntax coloring.
- Slide 4: Business Value & Measurable ROI (Tech & Marketing KPI cards).
- Slide 5: Summary Checklist + "Swipe/Save for Later" CTA.
- Compiles into `output/growth_carousel.pdf`.

### 4. Automated First-Comment Engagement Engine
- Generates an insightful First Comment containing official docs, GitHub repo links, or discussion prompts.
- Automatically dispatches the comment **120 seconds** after the main post goes live.
