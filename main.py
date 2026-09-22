"""Interactive Telegram Studio & LangGraph HITL Bot Loop.

Delivers the 5-slide carousel visual package (MediaGroup + PDF document + caption preview),
presents inline approval buttons, and handles natural language revisions with partial re-renders.
Supports CLI/Headless execution mode for scheduled cron environments.
"""

import os
import sys
import asyncio
import argparse
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from graph import build_growth_graph, PipelineState
from state import CarouselContent
from agents.dynamic_scheduler import get_dynamic_schedule

load_dotenv()

# Global state tracking for Telegram chat sessions
ACTIVE_THREADS: Dict[int, str] = {}
AWAITING_REVISION: Dict[int, bool] = {}


def get_thread_id(chat_id: int) -> str:
    """Returns a deterministic thread ID for chat checkpointing."""
    return f"telegram_studio_{chat_id}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start and displays platform status."""
    slot = get_dynamic_schedule()
    msg = (
        "🤖 *Autonomous Multi-Agent Growth Studio (Agency Grade)*\n\n"
        "Welcome! This system autonomously researches tech trends, synthesizes 5-slide "
        "dark-theme carousels, compiles LinkedIn PDFs, and gathers social analytics.\n\n"
        f"📅 *Next Scheduled Window:* `{slot.get('window_start')} - {slot.get('window_end')} BD Time`\n"
        f"🎯 *Calculated Slot:* `{slot.get('scheduled_time_display')}`\n\n"
        "Commands:\n"
        "• `/generate` - Trigger an autonomous draft generation\n"
        "• `/status` - View current checkpoint and analytics memory\n"
        "• `/help` - View instructions"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates a new carousel package up to the HITL interruption checkpoint."""
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(chat_id)
    ACTIVE_THREADS[chat_id] = thread_id
    AWAITING_REVISION[chat_id] = False

    status_msg = await update.message.reply_text("🔄 *Agents activated:* Researching trends and rendering carousel...", parse_mode="Markdown")

    app = build_growth_graph(enable_interrupt=True)
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: PipelineState = {
        "day_number": 14,
        "scheduled_slot": None,
        "topic": None,
        "past_exemplars": [],
        "carousel": None,
        "critique": None,
        "revision_count": 0,
        "revision_request": None,
        "rendered_images": [],
        "pdf_path": None,
        "human_approved": False,
        "skipped": False,
        "publication": None,
        "logs": [],
    }

    # Run up to human_review interruption
    for event in app.stream(initial_state, config=config):
        pass

    state = app.get_state(config)
    await send_carousel_preview(chat_id, context, state.values)
    await status_msg.delete()


async def send_carousel_preview(chat_id: int, context: ContextTypes.DEFAULT_TYPE, state_values: Dict[str, Any]):
    """Sends 5 carousel PNGs as a media group, the compiled PDF, and action buttons."""
    images = state_values.get("rendered_images", [])
    pdf_path = state_values.get("pdf_path")
    carousel_data = state_values.get("carousel", {})
    caption = carousel_data.get("post_caption", "No caption generated.")
    first_comment = carousel_data.get("first_comment", "No first comment generated.")
    critique = state_values.get("critique", {})

    # 1. Send Media Group (5 Images)
    if images and len(images) == 5:
        media_group = [InputMediaPhoto(open(img, "rb")) for img in images]
        media_group[0].caption = f"📊 *5-Slide Technical Carousel Preview (Day {carousel_data.get('day_number')})*"
        media_group[0].parse_mode = "Markdown"
        await context.bot.send_media_group(chat_id=chat_id, media=media_group)

    # 2. Send Compiled PDF
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            await context.bot.send_document(
                chat_id=chat_id,
                document=f,
                filename="growth_carousel.pdf",
                caption="📄 *Compiled LinkedIn Document (High-Retention PDF)*",
                parse_mode="Markdown",
            )

    # 3. Send Text Preview & Action Buttons
    critique_str = f"⭐ *Critic Score:* `{critique.get('score', 'N/A')}/10`\n"
    preview_msg = (
        f"{critique_str}\n"
        f"📝 *Main Post Caption Preview:*\n"
        f"```\n{caption[:500]}...\n```\n\n"
        f"💬 *Automated First Comment (Dispatched 120s post-publish):*\n"
        f"```\n{first_comment}\n```"
    )

    keyboard = [
        [
            InlineKeyboardButton("🚀 Approve & Post All", callback_data="approve_post"),
            InlineKeyboardButton("✏️ Interactive Revision", callback_data="request_revision"),
        ],
        [
            InlineKeyboardButton("⏭️ Skip Today", callback_data="skip_post"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text=preview_msg,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline buttons: Approve, Revise, and Skip."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    thread_id = ACTIVE_THREADS.get(chat_id, get_thread_id(chat_id))
    action = query.data

    app = build_growth_graph(enable_interrupt=True)
    config = {"configurable": {"thread_id": thread_id}}

    if action == "approve_post":
        await query.edit_message_text("🚀 *Draft Approved!* Dispatching to LinkedIn, Meta, and Instagram...", parse_mode="Markdown")
        app.update_state(config, {"human_approved": True, "skipped": False})
        for event in app.stream(None, config=config):
            pass

        state = app.get_state(config)
        pub = state.values.get("publication", {})
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"✅ *Published Successfully!*\n\n"
                f"• *Status:* `{pub.get('status')}`\n"
                f"• *LinkedIn URN:* `{pub.get('linkedin_urn')}`\n"
                f"• *Facebook ID:* `{pub.get('facebook_post_id')}`\n"
                f"• *Instagram ID:* `{pub.get('instagram_container_id')}`\n\n"
                f"⏳ *First Comment Engine:* Automated technical comment scheduled to drop in 120 seconds."
            ),
            parse_mode="Markdown",
        )

    elif action == "request_revision":
        AWAITING_REVISION[chat_id] = True
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "✏️ *Interactive Revision Mode Enabled*\n\n"
                "Please type your requested revision in plain text.\n"
                "Example: `Slide 3-এর কোড স্নিপেটে LangGraph latency উল্লেখ করো`\n"
                "The agent will execute a targeted re-render and return updated assets."
            ),
            parse_mode="Markdown",
        )

    elif action == "skip_post":
        app.update_state(config, {"skipped": True, "human_approved": False})
        for event in app.stream(None, config=config):
            pass
        await query.edit_message_text("⏭️ *Publication Skipped for Today.* Checkpoint stored.", parse_mode="Markdown")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles natural language revision text from the user."""
    chat_id = update.effective_chat.id
    if not AWAITING_REVISION.get(chat_id, False):
        return

    user_text = update.message.text.strip()
    AWAITING_REVISION[chat_id] = False
    thread_id = ACTIVE_THREADS.get(chat_id, get_thread_id(chat_id))

    status_msg = await update.message.reply_text(
        f"🔄 *Processing Revision:* \"{user_text}\"\nRe-synthesizing and rendering updated carousel...",
        parse_mode="Markdown",
    )

    app = build_growth_graph(enable_interrupt=True)
    config = {"configurable": {"thread_id": thread_id}}

    # Update state with revision request and resume
    app.update_state(config, {"revision_request": user_text, "human_approved": False})
    for event in app.stream(None, config=config):
        pass

    state = app.get_state(config)
    await send_carousel_preview(chat_id, context, state.values)
    await status_msg.delete()


# ------------------------------------------------------------------------------
# CLI / Headless Runner
# ------------------------------------------------------------------------------

def run_cli_mode(auto_approve: bool = False, revision_prompt: Optional[str] = None):
    """Runs the full pipeline in terminal mode for local testing or CI/CD crons."""
    print("=" * 70)
    print("AUTONOMOUS MULTI-AGENT GROWTH PLATFORM (CLI STUDIO)")
    print("=" * 70)

    thread_id = f"cli_session_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}
    app = build_growth_graph(enable_interrupt=not auto_approve)

    initial_state: PipelineState = {
        "day_number": 14,
        "scheduled_slot": None,
        "topic": None,
        "past_exemplars": [],
        "carousel": None,
        "critique": None,
        "revision_count": 0,
        "revision_request": None,
        "rendered_images": [],
        "pdf_path": None,
        "human_approved": auto_approve,
        "skipped": False,
        "publication": None,
        "logs": [],
    }

    print("[CLI] Executing workflow stream...")
    for event in app.stream(initial_state, config=config):
        node_name = list(event.keys())[0]
        print(f" -> Completed node: {node_name}")

    state = app.get_state(config)
    carousel = state.values.get("carousel", {})

    print("\n" + "=" * 70)
    print(f"CAROUSEL TITLE: {carousel.get('topic_headline')}")
    print(f"CRITIC SCORE:   {state.values.get('critique', {}).get('score')}/10")
    print(f"PDF COMPILED:   {state.values.get('pdf_path')}")
    print(f"SLIDES COUNT:   {len(state.values.get('rendered_images', []))}")
    print("=" * 70)

    if revision_prompt and not auto_approve:
        print(f"\n[CLI] Applying natural language revision: '{revision_prompt}'...")
        app.update_state(config, {"revision_request": revision_prompt, "human_approved": False})
        for event in app.stream(None, config=config):
            pass
        state = app.get_state(config)
        print("[CLI] Revision re-render complete!")

    if not auto_approve and state.next == ("human_review",):
        print("\n[CLI HITL Prompt]")
        print("Options: [1] Approve & Post All | [2] Skip Today")
        choice = "1"  # Default in headless verification
        if choice == "1":
            print("[CLI] Approving publication...")
            app.update_state(config, {"human_approved": True})
            for event in app.stream(None, config=config):
                pass
            state = app.get_state(config)
            print("[CLI] Publication completed successfully!")
            print(f"Publication result: {state.values.get('publication')}")
        else:
            print("[CLI] Skipped.")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Multi-Agent Growth Platform Studio")
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve publication without interruption")
    parser.add_argument("--revision", type=str, default=None, help="Optional revision prompt to test partial re-render")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if args.cli or not token:
        if not token and not args.cli:
            print("[Info] TELEGRAM_BOT_TOKEN not provided in .env. Running in interactive CLI mode.")
        run_cli_mode(auto_approve=args.auto_approve, revision_prompt=args.revision)
    else:
        print(f"[Telegram Studio] Starting Telegram Bot with token {token[:8]}...***")
        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", start_command))
        application.add_handler(CommandHandler("generate", generate_command))
        application.add_handler(CallbackQueryHandler(button_callback_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

        print("[Telegram Studio] Bot polling active. Send /start or /generate in your Telegram chat.")
        application.run_polling()


if __name__ == "__main__":
    main()
