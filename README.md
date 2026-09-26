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
- Generates an insightful First Comment containing discussion prompts and technical insights.
- Automatically dispatches the comment **120 seconds** after the main post goes live.

### 5. Authentic Portrait & Tipu Sultan Personal Branding
- Seamlessly integrates Tipu Sultan's verified authentic photo portrait into all 5 slides.
- Author badge: `Tipu Sultan | AI & Data Growth Architect • Day [N]` on every slide and post caption.

### 6. Strict Zero-Link Anti-Spam Architecture
- Eliminates all external URLs (`http://`, `https://`, `.com`, `.io`) across captions, slides, and comments to prevent algorithmic reach penalties.
- Establishes pure brand authority and drives engagement via technical discussion starters.

### 7. Permanent Facebook Page Security Lock
- Strictly locked to **Advance Digital Marketing Course** (Page ID: `105656909238175`).
- Multi-photo carousel album publishing with verified Page Access Token.
- Active security guardrail: refuses and aborts if any other Facebook page is targeted.

### 8. Infinite Lifetime Curriculum Engine & Cycle Mutation
- Comprehensive 24+ Master Class Syllabus covering GTM DataLayer, Meta CAPI, Stape.io, GA4 Server-Side, BigQuery, Shopify, and High-Ticket Retainers.
- **Dynamic Cycle Adaptation**: As days advance beyond Cycle 1, the system automatically adapts topic angles (e.g. Enterprise Debugging, Attribution Recovery, Automation Playbooks), mathematically guaranteeing 100% fresh, non-repeating content forever.

### 9. Telegram Mobile Command Center & Executive Bengali Decision Brief
- Runs continuously in background/daemon polling mode.
- Persistent mobile Reply Keyboard (docked bottom buttons) for one-tap operation:
  - `🚀 এক ক্লিকে পোস্ট তৈরি` (Generate Today's Draft)
  - `📅 আজকের দিন ও টপিক` (Topic & Day)
  - `📊 সিস্টেম স্ট্যাটাস` (System Status)
  - `🔑 মেটা টোকেন কন্ট্রোল` (Meta Token Control)
  - `⚙️ দিন পরিবর্তন` (Change Day)
  - `❓ সাহায্য ও গাইড` (Help & Guide)
- Delivers 7-section Bengali Executive Decision Briefing for at-a-glance post evaluation.
- Commands: `/start`, `/generate`, `/day`, `/setday <num>`, `/status`, `/token`, `/tokenstatus`, `/settoken <token>`, `/setappcreds <id> <secret>`, `/permtoken`, `/help`.
- Robust natural language handling: supports plain text triggers (`start`, `generate`, `status`, `day`, `1`, `2`) without needing slashes.
- Asynchronous non-blocking execution with `asyncio.to_thread`.

---

## 🔑 Permanent (Never-Expiring) Meta Access Token Guide

To permanently eliminate the hassle of recurring token expirations, use **Meta Business Suite System User Token** (Official 100% Never Expire solution):

1. Open [business.facebook.com](https://business.facebook.com) -> Click **Settings (Gear Icon)**.
2. Under **Users**, click **System Users** -> Click **Add**:
   - System User Name: `GrowthBot`
   - Role: `Admin`
3. Click **Assign Assets**:
   - Select Page: **Advance Digital Marketing Course** (Enable Full Control / Manage Page).
   - Select connected **Instagram Business Account**.
4. Click **Generate New Token** -> Select your Meta App.
5. 🌟 Under **Token Expiration**, select **"Never"** from the dropdown.
6. Check required permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
7. Click **Generate Token** and copy the generated token.
8. Paste it directly into your Telegram bot by clicking **"🔑 মেটা টোকেন কন্ট্রোল"** -> **"🔑 নতুন টোকেন পেস্ট করুন"** or sending `/settoken <your_token>`.

*Result:* This token will **NEVER EXPIRE** and provides lifetime 24/7 automated posting!

---

## 🖥️ Background 24/7 Operation on Windows

To run the bot silently in the background so you can control it anytime from your smartphone:

- **Start in Background:** Double-click `start_bot_background.bat` (runs supervisor silently with auto-restart on crashes).
- **Stop Background Bot:** Double-click `stop_bot.bat`.
- **Live Logs:** Inspect `data\bot.log`.


