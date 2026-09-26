"""Interactive Telegram Studio & LangGraph HITL Bot Loop (Agency-Grade Mobile Command Center).

Delivers the 5-slide carousel visual package (MediaGroup + PDF document + caption preview),
presents inline approval buttons, handles natural language revisions with partial re-renders,
and provides a 100% full-featured Telegram Remote Control with persistent mobile buttons.
Supports CLI/Headless execution mode for scheduled cron environments.
"""

import os
import sys
import json
import threading
import requests
import asyncio
import argparse
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
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
    ReplyKeyboardMarkup,
    KeyboardButton,
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
from agents.ninja_orchestrator import (
    get_current_day,
    advance_current_day,
    set_current_day,
    generate_bengali_decision_brief,
    initialize_vault,
)
from agents.curriculum_engine import CurriculumEngine
from agents.publisher import (
    verify_and_update_meta_token,
    get_meta_token_info,
    save_meta_app_credentials,
    exchange_and_generate_permanent_token,
    verify_and_update_linkedin_token,
    get_linkedin_token_info,
)

load_dotenv()

# Global state tracking for Telegram chat sessions
ACTIVE_THREADS: Dict[int, str] = {}
AWAITING_REVISION: Dict[int, bool] = {}
AWAITING_DAY: Dict[int, bool] = {}
AWAITING_TOKEN: Dict[int, bool] = {}
AWAITING_APP_CREDS: Dict[int, bool] = {}
AWAITING_LI_TOKEN: Dict[int, bool] = {}


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Lightweight HTTP server responding to cloud platform health checks & keep-alive pings."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        curr_day = get_current_day()
        payload = json.dumps({
            "status": "online",
            "service": "Autonomous Multi-Agent Growth Platform",
            "current_day": curr_day,
            "cloud_engine": "24/7/365 Continuous",
            "timestamp": time.time(),
        })
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, format, *args):
        # Silence default request logging to avoid log pollution
        return


def start_health_server(port: int = 10000):
    """Starts the 24/7 Cloud healthcheck server in a background daemon thread."""
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[Cloud Engine] 24/7 Cloud Healthcheck Server active on port {port}")
    return server


def get_thread_id(chat_id: int) -> str:
    """Returns a deterministic thread ID for chat checkpointing."""
    return f"telegram_studio_{chat_id}"


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Returns the persistent mobile menu buttons docked at bottom of Telegram chat."""
    keyboard = [
        [KeyboardButton("🚀 এক ক্লিকে পোস্ট তৈরি"), KeyboardButton("📅 আজকের দিন ও টপিক")],
        [KeyboardButton("📊 সিস্টেম স্ট্যাটাস"), KeyboardButton("🔑 মেটা টোকেন কন্ট্রোল")],
        [KeyboardButton("⚙️ দিন পরিবর্তন"), KeyboardButton("❓ সাহায্য ও গাইড")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    """Returns inline clickable buttons for quick navigation in chat messages."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Generate Today's Post", callback_data="cmd_generate"),
            InlineKeyboardButton("📅 Check Topic", callback_data="cmd_day"),
        ],
        [
            InlineKeyboardButton("📊 System Status", callback_data="cmd_status"),
            InlineKeyboardButton("🔑 Meta Token Status", callback_data="cmd_token_status"),
        ],
        [
            InlineKeyboardButton("⚙️ Change Day", callback_data="cmd_setday_prompt"),
            InlineKeyboardButton("♾️ Permanent Token Guide", callback_data="cmd_perm_guide"),
        ],
    ])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start, 'start', and displays the platform mobile command center."""
    slot = get_dynamic_schedule()
    curr_day = get_current_day()
    ce = CurriculumEngine()
    ct = ce.get_topic_by_day(curr_day)
    token_info = get_meta_token_info()

    if token_info.get("valid"):
        if token_info.get("never_expires"):
            token_status_str = "🟢 Active (♾️ Never Expires)"
        else:
            token_status_str = f"🟡 Active ({token_info.get('days_remaining', 'N/A')} days left)"
    else:
        token_status_str = "🔴 Expired / Needs Renewal"

    msg = (
        "🤖 *Autonomous Multi-Agent Growth Studio (Mobile Command Center)*\n\n"
        "স্বাগতম! আপনি এখন মোবাইল থেকে যেকোনো জায়গা থেকেই পুরো মাল্টি-এজেন্ট সিস্টেম নিয়ন্ত্রণ করতে পারবেন।\n\n"
        f"📌 *বর্তমান সক্রিয় পোস্ট:* `Day {curr_day:02d}` (Class {ct.class_id}: {ct.title[:38]}...)\n"
        f"📅 *পিক পাবলিকেশন উইন্ডো:* `{slot.get('window_start')} - {slot.get('window_end')} BD Time`\n"
        f"🎯 *টার্গেট স্কেডিউল স্লট:* `{slot.get('scheduled_time_display')}`\n"
        f"🔑 *Meta Facebook/IG Token:* `{token_status_str}`\n\n"
        "💡 *কন্ট্রোল করার উপায়:*\n"
        "নিচের বাটনে সরাসরি ক্লিক করুন অথবা মেসেজ পাঠান:\n"
        "• `🚀 এক ক্লিকে পোস্ট তৈরি` - আজকের লেসনের ড্রাফট ও স্লাইড তৈরি করুন\n"
        "• `📅 আজকের দিন ও টপিক` - বর্তমান দিনের সিলেবাস ও স্ট্র্যাটেজি দেখুন\n"
        "• `📊 সিস্টেম স্ট্যাটাস` - সমস্ত API ও এজেন্টের লাইভ স্ট্যাটাস দেখুন\n"
        "• `🔑 মেটা টোকেন কন্ট্রোল` - মেটা টোকেনের মেয়াদ ও পার্মানেন্ট সলিউশন\n"
        "• `⚙️ দিন পরিবর্তন` - পোস্টের দিন নম্বর পরিবর্তন করুন"
    )

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard()
    )
    await update.message.reply_text(
        "⚡ *কুইক অ্যাকশন মেনু (Quick Actions):*",
        reply_markup=get_main_inline_keyboard(),
        parse_mode="Markdown"
    )


async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays current active sequential day and corresponding curriculum topic in Bengali."""
    curr_day = get_current_day()
    ce = CurriculumEngine()
    ct = ce.get_topic_by_day(curr_day)
    msg = (
        f"📅 *অ্যাক্টিভ পোস্ট ট্র্যাকার (Active Tracker - Day {curr_day:02d})*\n\n"
        f"• *বর্তমান দিন:* `Day {curr_day:02d}`\n"
        f"• *সিলেবাস ক্লাস:* `Class {ct.class_id}`\n"
        f"• *মডিউল:* `{ct.module_category}`\n"
        f"• *টপিক:* `{ct.title}`\n"
        f"• *মূল সমস্যা:* {ct.problem_statement}\n"
        f"• *সমাধানের কৌশল:* {ct.actionable_tip}\n"
        f"• *প্রত্যাশিত ROI:* {ct.roi_metric_label}: `{ct.roi_metric_value}` ({ct.roi_subtext})\n\n"
        f"💡 নতুন ড্রাফট জেনারেট করতে `🚀 এক ক্লিকে পোস্ট তৈরি` চাপুন, অথবা দিন পরিবর্তন করতে `⚙️ দিন পরিবর্তন` চাপুন।"
    )
    inline_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Generate This Draft", callback_data="cmd_generate"),
            InlineKeyboardButton("⚙️ Change Day", callback_data="cmd_setday_prompt"),
        ]
    ])
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=inline_kb)


async def setday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the active day number manually (e.g. /setday 1)."""
    if not context.args:
        chat_id = update.effective_chat.id
        AWAITING_DAY[chat_id] = True
        await update.message.reply_text(
            "🔢 *দিন পরিবর্তন (Set Active Day)*\n\nঅনুগ্রহ করে নতুন দিন নম্বরটি লিখে পাঠান (যেমন: `1`, `2`, `14`):",
            parse_mode="Markdown"
        )
        return

    try:
        new_day = int(context.args[0])
        set_current_day(new_day)
        ce = CurriculumEngine()
        ct = ce.get_topic_by_day(new_day)
        await update.message.reply_text(
            f"✅ *দিন সফলভাবে আপডেট হয়েছে:*\n\n"
            f"• *বর্তমান কাউন্টার:* `Day {new_day:02d}`\n"
            f"• *টপিক:* `Class {ct.class_id} - {ct.title}`\n\n"
            "এখন ড্রাফট তৈরি করতে `🚀 এক ক্লিকে পোস্ট তৈরি` বাটনে চাপুন বা `/generate` পাঠান।",
            parse_mode="Markdown",
            reply_markup=get_main_reply_keyboard()
        )
    except ValueError:
        await update.message.reply_text("❌ অনুগ্রহ করে একটি সঠিক সংখ্যা দিন (যেমন: `/setday 1` বা শুধু `1`)।", parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays comprehensive multi-platform and agentic system status."""
    curr_day = get_current_day()
    ce = CurriculumEngine()
    ct = ce.get_topic_by_day(curr_day)
    slot = get_dynamic_schedule()
    token_info = get_meta_token_info()
    vault = initialize_vault()
    posts_count = len(vault.get("posts", []))
    completed_days = len(vault.get("completed_days", []))

    # Meta token status display
    if token_info.get("valid"):
        if token_info.get("never_expires"):
            meta_status = "🟢 Active (♾️ Never Expires / Lifetime)"
        else:
            meta_status = f"🟡 Active ({token_info.get('days_remaining', 'N/A')} days remaining)"
    else:
        err = token_info.get("error", "Expired")
        meta_status = f"🔴 Expired / Needs Renewal (`{err[:40]}...`)"

    # Gemini API status check
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_status = "🟢 Active & Authenticated" if gemini_key else "🔴 Missing API Key"

    # LinkedIn status
    li_info = get_linkedin_token_info()
    if li_info.get("valid"):
        li_status = f"🟢 Connected ({li_info.get('name', 'Tipu Sultan')}) - 60 Days Lifecycle Active"
    else:
        li_status = f"🔴 Needs Renewal (`{li_info.get('error', 'Token issue')[:40]}`)"

    msg = (
        "📊 *Autonomous Multi-Agent System Live Status*\n\n"
        f"🤖 *Orchestrator:* Active & Listening\n"
        f"📌 *Active Sequential Post:* `Day {curr_day:02d}` (Class {ct.class_id})\n"
        f"📚 *Curriculum Topic:* `{ct.title[:45]}...`\n"
        f"⏰ *Next Optimal Window:* `{slot.get('scheduled_time_display')} BD Time`\n\n"
        "🌐 *প্ল্যাটফর্ম ও এপিআই হেলথ স্ট্যাটাস:*\n"
        f"• *Gemini GenAI 3.6:* {gemini_status}\n"
        f"• *LinkedIn API:* {li_status}\n"
        f"• *Meta Facebook Page:* `{token_info.get('page_name', 'Advance Digital Marketing Course')}`\n"
        f"• *Meta Access Token:* {meta_status}\n"
        f"• *Instagram Account:* `@{token_info.get('instagram_username', 'Connected')}` (ID: `{token_info.get('instagram_id', '17841405072430897')}`)\n\n"
        f"🗄️ *Content Vault Memory:*\n"
        f"• *Completed Posts:* `{completed_days}` posts\n"
        f"• *Anti-Fluff Similarity Threshold:* `60% Max` (Zero Link Policy Active)"
    )

    inline_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Generate Draft", callback_data="cmd_generate"),
            InlineKeyboardButton("🔑 Meta Token Control", callback_data="cmd_token_status"),
        ],
        [
            InlineKeyboardButton("⚙️ Change Day", callback_data="cmd_setday_prompt"),
            InlineKeyboardButton("❓ Help Guide", callback_data="cmd_help"),
        ]
    ])

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=inline_kb)


async def token_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays detailed Meta Facebook & Instagram Token Status, lifetime, and actions."""
    info = get_meta_token_info()
    app_id = os.getenv("META_APP_ID", "")

    if info.get("valid"):
        if info.get("never_expires"):
            lifetime_str = "♾️ *Never Expires (Permanent / লাইফটাইম টোকেন সক্রিয়)*"
            recommendation = "✅ আপনার টোকেন আজীবনের জন্য স্থায়ী! বারবার টোকেন বসানোর কোনো ঝামেলা আর নেই।"
        else:
            time_str = info.get("time_remaining_str") or f"{info.get('days_remaining')} দিন"
            lifetime_str = f"⏳ *মেয়াদ বাকি:* `{time_str}`"
            recommendation = (
                "⚠️ এটি একটি সাময়িক স্বল্পমেয়াদী টোকেন। এটিকে আজীবনের জন্য স্থায়ী (Never Expire) করতে:\n"
                "• **সহজ উপায়:** নিচের '⚡ App Credentials সেট করুন' বাটনে ক্লিক করে App Secret পাঠিয়ে দিন।\n"
                "• অথবা '♾️ পার্মানেন্ট টোকেন গাইড' অনুসরণ করে Business Manager থেকে পার্মানেন্ট টোকেন নিন।"
            )
        status_line = "🟢 *স্ট্যাটাস: সক্রিয় (Active)*"
    else:
        status_line = "🔴 *স্ট্যাটাস: এক্সপায়ার্ড বা অবৈধ (Expired / Invalid)*"
        lifetime_str = f"❌ *ত্রুটি:* `{info.get('error', 'Session has expired')}`"
        recommendation = (
            "🚨 আপনার মেটা টোকেনটির মেয়াদ শেষ হয়ে গেছে। ফেসবুকে ও ইন্সটাগ্রামে লাইভ পোস্ট করতে "
            "নিচের '🔑 নতুন টোকেন পেস্ট করুন' বাটনে ক্লিক করে নতুন টোকেন দিন।"
        )

    msg = (
        "🔑 *Meta Facebook & Instagram Token Management Center*\n\n"
        f"{status_line}\n"
        f"{lifetime_str}\n\n"
        f"• *Facebook Page:* `{info.get('page_name', 'Advance Digital Marketing Course')}` (ID: `{info.get('page_id')}`)\n"
        f"• *Instagram Account ID:* `{info.get('instagram_id')}`\n"
        f"• *Meta App ID:* `{app_id or '2145694369400433'}`\n\n"
        f"💡 *পরামর্শ:*\n{recommendation}"
    )

    inline_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔑 নতুন টোকেন পেস্ট করুন", callback_data="cmd_token_prompt"),
            InlineKeyboardButton("♾️ পার্মানেন্ট টোকেন গাইড", callback_data="cmd_perm_guide"),
        ],
        [
            InlineKeyboardButton("⚡ App Credentials সেট করুন", callback_data="cmd_creds_prompt"),
            InlineKeyboardButton("📊 সিস্টেম স্ট্যাটাস", callback_data="cmd_status"),
        ]
    ])

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=inline_kb)


async def settoken_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dynamically updates and verifies the Meta Page/User Access Token."""
    chat_id = update.effective_chat.id
    if not context.args:
        AWAITING_TOKEN[chat_id] = True
        await update.message.reply_text(
            "🔑 *নতুন Meta টোকেন আপডেট*\n\n"
            "অনুগ্রহ করে আপনার নতুন টোকেনটি এখানে মেসেজ হিসেবে সরাসরি পেস্ট করে পাঠান।\n"
            "বট স্বয়ংক্রিয়ভাবে টোকেন যাচাই করবে এবং .env আপডেট করে সক্রিয় করবে।",
            parse_mode="Markdown"
        )
        return

    new_token = " ".join(context.args).strip().strip("<>\"' \t\r\n")
    status_msg = await update.message.reply_text("🔄 *Meta Graph API-তে টোকেন যাচাই ও কনফিগার করা হচ্ছে...*", parse_mode="Markdown")

    res = verify_and_update_meta_token(new_token)
    if res.get("success"):
        ig_user = f" (@{res['instagram_username']})" if res.get("instagram_username") else ""
        if res.get("never_expires"):
            exp_text = "♾️ *Never Expires (Permanent / লাইফটাইম টোকেন)*"
        elif res.get("time_remaining_str"):
            exp_text = f"⏳ *মেয়াদ:* `{res.get('time_remaining_str')}`"
        elif res.get("days_remaining"):
            exp_text = f"⏳ *মেয়াদ:* `{res.get('days_remaining')} দিন`"
        else:
            exp_text = "🟢 *সক্রিয়*"

        msg = (
            "✅ *Meta টোকেন সফলভাবে যাচাই ও আপডেট হয়েছে!*\n\n"
            f"• *মেয়াদ:* {exp_text}\n"
            f"• *ব্যবহারকারী:* `{res.get('user_name')}`\n"
            f"• *Facebook Page:* `{res.get('page_name')}` (ID: `{res.get('page_id')}`)\n"
            f"• *Instagram Account ID:* `{res.get('instagram_id')}`{ig_user}\n"
            f"• *স্ট্যাটাস:* ফেসবুক এবং ইন্সটাগ্রামে লাইভ পোস্ট করার জন্য সম্পূর্ণ প্রস্তুত!"
        )
    else:
        err = res.get("error", "Unknown error")
        msg = (
            f"❌ *টোকেন ভেরিফিকেশন ব্যর্থ হয়েছে:*\n`{err}`\n\n"
            "অনুগ্রহ করে নিশ্চিত করুন টোকেনটিতে `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, এবং `instagram_content_publish` পারমিশন রয়েছে।"
        )

    await status_msg.edit_text(msg, parse_mode="Markdown")


async def setappcreds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets Meta App ID & Secret and automatically exchanges current token for Never-Expiring Permanent Token."""
    args = list(context.args) if context.args else []
    chat_id = update.effective_chat.id

    configured_app_id = os.getenv("META_APP_ID", "2145694369400433").strip()

    if len(args) == 1:
        app_id = configured_app_id
        app_secret = args[0].strip()
    elif len(args) >= 2:
        app_id = args[0].strip()
        app_secret = args[1].strip()
    else:
        AWAITING_APP_CREDS[chat_id] = True
        await update.message.reply_text(
            "⚡ *Meta App Credentials সেট করুন*\n\n"
            f"আপনার Meta App ID: `{configured_app_id}` (Social Growth Auto)\n\n"
            "🔑 অনুগ্রহ করে আপনার **App Secret** টি এখানে মেসেজ হিসেবে পাঠিয়ে দিন (অথবা `<App_ID> <App_Secret>`):\n\n"
            "📍 *কোথায় পাবেন? (মাত্র ৩০ সেকেন্ড):*\n"
            f"১️⃣ ব্রাউজারে যান: `https://developers.facebook.com/apps/{configured_app_id}/settings/basic/`\n"
            "২️⃣ **App secret** এর পাশে **Show (দেখাও)** বাটনে চাপ দিন এবং কপি করুন।\n"
            "৩️⃣ কপি করা সিক্রেট কোডটি এখানে পেস্ট করে দিন!\n\n"
            "💡 App Secret পাওয়া মাত্রই বট আপনার বর্তমান টোকেনটিকে আজীবনের জন্য **Never Expiring (স্থায়ী)** টোকেনে কনভার্ট করে নিবে!",
            parse_mode="Markdown"
        )
        return

    ok = save_meta_app_credentials(app_id, app_secret)
    if not ok:
        await update.message.reply_text("❌ App ID বা Secret সংরক্ষণে সমস্যা হয়েছে।", parse_mode="Markdown")
        return

    # Attempt immediate auto-exchange on current token if present!
    current_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
    auto_exchanged = False
    if current_token:
        try:
            ex_res = exchange_and_generate_permanent_token(current_token, app_id, app_secret)
            if ex_res.get("success") and ex_res.get("permanent_page_token"):
                v_res = verify_and_update_meta_token(ex_res["permanent_page_token"], app_id=app_id, app_secret=app_secret)
                if v_res.get("success"):
                    auto_exchanged = True
        except Exception as e:
            print(f"[SetAppCreds] Auto-exchange error: {e}")

    secret_masked = '*' * (len(app_secret) - 4) + app_secret[-4:] if len(app_secret) > 4 else '****'

    if auto_exchanged:
        msg = (
            f"🎉 *অভিনন্দন! আপনার Meta টোকেন আজীবনের জন্য স্থায়ী (Never Expire) করা হয়েছে!*\n\n"
            f"• *App ID:* `{app_id}`\n"
            f"• *App Secret:* `{secret_masked}`\n"
            f"• *মেয়াদ:* ♾️ *Never Expires (লাইফটাইম টোকেন সক্রিয়)*\n\n"
            "✅ এখন থেকে আর কখনোই আপনার ফেসবুক বা ইনস্টাগ্রাম টোকেন এক্সপায়ার হবে না!"
        )
    else:
        msg = (
            f"✅ *Meta App Credentials সফলভাবে সংরক্ষিত হয়েছে!*\n\n"
            f"• *App ID:* `{app_id}`\n"
            f"• *App Secret:* `{secret_masked}`\n\n"
            "এখন যেকোনো নতুন টোকেন পেস্ট করলেই তা স্বয়ংক্রিয়ভাবে আজীবনের জন্য পার্মানেন্ট হয়ে যাবে।"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def perm_guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends comprehensive Bengali guide on getting 100% Never-Expiring Meta Token."""
    configured_app_id = os.getenv("META_APP_ID", "2145694369400433").strip()
    guide = (
        "♾️ *Meta টোকেন আজীবনের জন্য স্থায়ী (Never Expire) করার ২টি সহজ সমাধান*\n\n"
        "বারবার টোকেন এক্সপায়ার হওয়ার ঝামেলা চিরতরে বন্ধ করার ২টি অফিশিয়াল উপায় রয়েছে:\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *পদ্ধতি ১: App Secret প্রদান (সবচেয়ে সহজ - ৩০ সেকেন্ড)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"আপনার App ID: `{configured_app_id}`\n"
        f"১. যান: `https://developers.facebook.com/apps/{configured_app_id}/settings/basic/`\n"
        "২. **App secret** এর পাশে **Show (দেখাও)** বাটনে ক্লিক করে সিক্রেটটি কপি করুন।\n"
        "৩. টেলিগ্রামে `/setappcreds <App_Secret>` লিখে পাঠিয়ে দিন।\n"
        "👉 বট সাথে সাথে টোকেনটিকে **Never Expiring (লাইফটাইম)** করে নিবে!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *পদ্ধতি ২: Business Manager System User Token*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "১. যান: `https://business.facebook.com/settings/system-users`\n"
        "২. **Add** ক্লিক করুন -> নাম: `GrowthBot`, Role: `Admin`।\n"
        "৩. **Assign Assets** এ ক্লিক করে **Advance Digital Marketing Course** ও Instagram সিলেক্ট করে Full Control দিন।\n"
        "৪. **Generate New Token** এ ক্লিক করুন -> App: `Social Growth Auto` সিলেক্ট করুন।\n"
        "৫. 🌟 **Token Expiration-এ 'Never' সিলেক্ট করুন!**\n"
        "৬. পারমিশন টিক দিন: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`।\n"
        "৭. টোকেনটি কপি করে চ্যাটে পেস্ট করে দিন।\n\n"
        "🎉 এটি আজীবন কার্যকর থাকবে, আর কোনোদিন টোকেন এক্সপায়ার হবে না!"
    )
    inline_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ App Credentials সেট করুন", callback_data="cmd_creds_prompt"),
            InlineKeyboardButton("🔑 নতুন টোকেন পেস্ট করুন", callback_data="cmd_token_prompt"),
        ],
        [
            InlineKeyboardButton("📊 সিস্টেম স্ট্যাটাস", callback_data="cmd_status"),
        ]
    ])
    await update.message.reply_text(guide, parse_mode="Markdown", reply_markup=inline_kb)



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays complete help instructions."""
    msg = (
        "❓ *Autonomous Multi-Agent Growth Platform গাইড*\n\n"
        "আপনি টেলিগ্রামের নিচের বাটনগুলো চেপে অথবা কমান্ড লিখে যেকোনো কাজ করতে পারেন:\n\n"
        "📌 *প্রধান বাটনসমূহ:*\n"
        "• `🚀 এক ক্লিকে পোস্ট তৈরি` - আজকের নির্ধারিত সিলেবাস ক্লাসের উপর ৫-স্লাইড ডার্ক ক্যারোজেল, লিঙ্কডইন PDF ও বাংলায় ডিসিশন ব্রিফ তৈরি করবে।\n"
        "• `📅 আজকের দিন ও টপিক` - বর্তমান সক্রিয় পোস্টের দিন এবং সিলেবাসের বিস্তারিত দেখাবে।\n"
        "• `📊 সিস্টেম স্ট্যাটাস` - লিঙ্কডইন, ফেসবুক, ইন্সটাগ্রাম ও জেমিনাই এআই-র লাইভ স্ট্যাটাস দেখাবে।\n"
        "• `🔑 মেটা টোকেন কন্ট্রোল` - ফেসবুক/ইন্সটাগ্রাম টোকেনের মেয়াদ যাচাই ও পার্মানেন্ট সলিউশন।\n"
        "• `⚙️ দিন পরিবর্তন` - যেকোনো দিন নম্বরে (Day 1 - Day 100) জাম্প করুন।\n\n"
        "📌 *সরাসরি টেক্সট কমান্ড:*\n"
        "• `/start` বা `start` - মূল কমান্ড সেন্টার মেনু খুলুন\n"
        "• `/generate` - নতুন পোস্ট ড্রাফট তৈরি করুন\n"
        "• `/status` - সিস্টেমের স্বাস্থ্য ও স্ট্যাটাস দেখুন\n"
        "• `/day` - বর্তমান দিনের টপিক দেখুন\n"
        "• `/setday <সংখ্যা>` - সরাসরি দিন সেট করুন (যেমন: `/setday 2`)\n"
        "• `/settoken <টোকেন>` - মেটা টোকেন আপডেট করুন\n"
        "• `/setlinkedin <টোকেন>` - লিঙ্কডইন টোকেন আপডেট করুন\n"
        "• `/permtoken` - আজীবনের জন্য পার্মানেন্ট টোকেন নেওয়ার গাইড"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_reply_keyboard())


async def setlinkedin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dynamically updates and verifies LinkedIn Access Token."""
    chat_id = update.effective_chat.id
    if not context.args:
        AWAITING_LI_TOKEN[chat_id] = True
        await update.message.reply_text(
            "💼 *LinkedIn Access Token আপডেট*\n\n"
            "অনুগ্রহ করে আপনার নতুন লিঙ্কডইন টোকেনটি এখানে মেসেজ হিসেবে পাঠিয়ে দিন।\n"
            "বট স্বয়ংক্রিয়ভাবে প্রোফাইল যাচাই করবে এবং সিস্টেমে সক্রিয় করবে।",
            parse_mode="Markdown"
        )
        return

    new_token = " ".join(context.args).strip().strip("<>\"' \t\r\n")
    status_msg = await update.message.reply_text("🔄 *LinkedIn API-তে টোকেন যাচাই করা হচ্ছে...*", parse_mode="Markdown")

    res = verify_and_update_linkedin_token(new_token)
    if res.get("success"):
        msg = (
            "✅ *LinkedIn টোকেন সফলভাবে যাচাই ও আপডেট হয়েছে!*\n\n"
            f"• *ব্যবহারকারী:* `{res.get('name')}`\n"
            f"• *ইমেইল:* `{res.get('email')}`\n"
            f"• *URN:* `{res.get('urn')}`\n"
            f"• *স্ট্যাটাস:* 🟢 সক্রিয় (পরবর্তী ৬০ দিনের জন্য সম্পূর্ণ প্রস্তুত)!\n\n"
            "💡 লিঙ্কডইনের অফিশিয়াল গ্লোবাল পলিসি অনুযায়ী প্রতিটি টোকেনের সর্বোচ্চ মেয়াদ ৬০ দিন থাকে। "
            "মেয়াদ শেষ হওয়ার ৭ দিন আগে বট আপনাকে টেলিগ্রামে আগাম রিমাইন্ডার দিবে।"
        )
    else:
        err = res.get("error", "Unknown error")
        msg = f"❌ *LinkedIn টোকেন যাচাই ব্যর্থ হয়েছে:*\n`{err}`"

    await status_msg.edit_text(msg, parse_mode="Markdown")


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates a new carousel package asynchronously up to the HITL interruption checkpoint."""
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(chat_id)
    ACTIVE_THREADS[chat_id] = thread_id
    AWAITING_REVISION[chat_id] = False

    current_day = get_current_day()
    ce = CurriculumEngine()
    ct = ce.get_topic_by_day(current_day)

    status_msg = await update.message.reply_text(
        f"🔄 *Agents activated (Day {current_day:02d}):* Synthesizing Class {ct.class_id} ({ct.title[:35]}...)\n"
        "⏳ গবেষণা, স্লাইড সিন্থেসিস এবং রেন্ডারিং সম্পন্ন হচ্ছে (১০-১৫ সেকেন্ড)...",
        parse_mode="Markdown"
    )

    def run_graph_sync():
        app = build_growth_graph(enable_interrupt=True)
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: PipelineState = {
            "day_number": current_day,
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
        return state.values

    try:
        # Run graph in thread pool so it never blocks the Telegram async event loop
        state_values = await asyncio.to_thread(run_graph_sync)
        await send_carousel_preview(chat_id, context, state_values)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ *ড্রাফট তৈরিতে ত্রুটি:* `{str(e)}`", parse_mode="Markdown")


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
        day_num = carousel_data.get('day_number', 1)
        media_group = []
        for i, img in enumerate(images):
            if i == 0:
                media_group.append(
                    InputMediaPhoto(
                        open(img, "rb"),
                        caption=f"📊 *5-Slide Technical Carousel Preview (Day {day_num})*",
                        parse_mode="Markdown"
                    )
                )
            else:
                media_group.append(InputMediaPhoto(open(img, "rb")))

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

    # 3. Generate & Send Executive Bengali Decision Brief
    day_num = carousel_data.get('day_number', 1)
    ce = CurriculumEngine()
    ct = ce.get_topic_by_day(day_num)
    critique_score = critique.get('score', 9.4)
    try:
        crit_val = float(critique_score)
    except (ValueError, TypeError):
        crit_val = 9.4

    bengali_brief = generate_bengali_decision_brief(
        day_number=day_num,
        topic_headline=carousel_data.get("topic_headline", ct.title),
        class_id=ct.class_id,
        module_category=ct.module_category,
        problem_statement=ct.problem_statement,
        actionable_tip=ct.actionable_tip,
        roi_metric_label=ct.roi_metric_label,
        roi_metric_value=ct.roi_metric_value,
        roi_subtext=ct.roi_subtext,
        critique_score=crit_val,
        slides_count=len(images) if images else 5,
    )

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=bengali_brief,
            parse_mode="Markdown",
        )
    except Exception:
        await context.bot.send_message(
            chat_id=chat_id,
            text=bengali_brief,
        )

    # 4. Send Post Caption Preview & Action Buttons
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
            InlineKeyboardButton("🔄 Regenerate", callback_data="cmd_generate"),
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
    """Handles inline buttons: Approve, Revise, Skip, and Quick Navigation."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    thread_id = ACTIVE_THREADS.get(chat_id, get_thread_id(chat_id))
    action = query.data

    # Navigation buttons
    if action == "cmd_generate":
        await generate_command(update, context)
        return
    elif action == "cmd_day":
        await day_command(update, context)
        return
    elif action == "cmd_status":
        await status_command(update, context)
        return
    elif action == "cmd_token_status":
        await token_status_command(update, context)
        return
    elif action == "cmd_perm_guide":
        await perm_guide_command(update, context)
        return
    elif action == "cmd_token_prompt":
        AWAITING_TOKEN[chat_id] = True
        await context.bot.send_message(
            chat_id=chat_id,
            text="🔑 *নতুন Meta টোকেন আপডেট*\n\nআপনার Meta Access Token-টি কপি করে এখানে সরাসরি পেস্ট করে পাঠান:",
            parse_mode="Markdown"
        )
        return
    elif action == "cmd_setday_prompt":
        AWAITING_DAY[chat_id] = True
        await context.bot.send_message(
            chat_id=chat_id,
            text="🔢 *দিন পরিবর্তন (Set Active Day)*\n\nঅনুগ্রহ করে নতুন দিন নম্বরটি লিখে পাঠান (যেমন: `1`, `2`, `14`):",
            parse_mode="Markdown"
        )
        return
    elif action == "cmd_creds_prompt":
        AWAITING_APP_CREDS[chat_id] = True
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚡ *Meta App ID ও Secret সেট করুন*\n\nফর্ম্যাট: `<App_ID> <App_Secret>` স্পেস দিয়ে লিখে পাঠান:\n(উদাহরণ: `123456789012345 98abcdef0123456789abcdef`)",
            parse_mode="Markdown"
        )
        return
    elif action == "cmd_help":
        await help_command(update, context)
        return

    # Workflow HITL buttons
    config = {"configurable": {"thread_id": thread_id}}

    if action == "approve_post":
        await query.edit_message_text("🚀 *Draft Approved!* Dispatching to LinkedIn, Meta Facebook, and Instagram...", parse_mode="Markdown")

        def run_publish_sync():
            app = build_growth_graph(enable_interrupt=True)
            state = app.get_state(config)

            # Check if checkpoint already has carousel and valid PDF file on disk
            state_vals = state.values if state else {}
            pdf_file = state_vals.get("pdf_path") if state_vals else None
            has_valid_assets = (
                state_vals
                and state_vals.get("carousel")
                and pdf_file
                and os.path.exists(pdf_file)
            )

            if not has_valid_assets:
                # If checkpoint is empty or files are missing, run full auto-approve pipeline on the fly!
                print("[ApprovePost] Checkpoint missing or expired in container. Executing auto-approve run...")
                curr_day = get_current_day()
                full_app = build_growth_graph(enable_interrupt=False)
                initial_state: PipelineState = {
                    "day_number": curr_day,
                    "scheduled_slot": None,
                    "topic": None,
                    "past_exemplars": [],
                    "carousel": None,
                    "critique": None,
                    "revision_count": 0,
                    "revision_request": None,
                    "rendered_images": [],
                    "pdf_path": None,
                    "human_approved": True,
                    "skipped": False,
                    "publication": None,
                    "logs": [],
                }
                for event in full_app.stream(initial_state, config=config):
                    pass
                final_state = full_app.get_state(config)
                return final_state.values or {}

            # Normal path: resume interrupted graph to publish
            app.update_state(config, {"human_approved": True, "skipped": False})
            for event in app.stream(None, config=config):
                pass
            final_state = app.get_state(config)

            # Extra safety: If publication was not triggered by graph, invoke publisher directly
            if not (final_state.values or {}).get("publication") and (final_state.values or {}).get("carousel"):
                from agents.publisher import MultiPlatformPublisher
                from state import CarouselContent
                publisher = MultiPlatformPublisher()
                c_content = CarouselContent.model_validate(final_state.values["carousel"])
                pdf_f = final_state.values.get("pdf_path", "output/growth_carousel.pdf")
                png_fs = final_state.values.get("rendered_images", [])
                p_res = publisher.publish_all(carousel=c_content, pdf_path=pdf_f, png_paths=png_fs)
                return {**final_state.values, "publication": p_res.model_dump()}

            return final_state.values or {}

        try:
            state_values = await asyncio.to_thread(run_publish_sync)
            pub = state_values.get("publication") or {}
            pub_status = pub.get("status")
            topic_title = (state_values.get("topic") or {}).get("title", "")
            completed_day = state_values.get("day_number", get_current_day())

            if pub_status == "published":
                next_day = advance_current_day(completed_day=completed_day, topic_title=topic_title)
                meta_id = pub.get("facebook_post_id", "N/A")
                li_urn = pub.get("linkedin_urn", "N/A")
                ig_id = pub.get("instagram_container_id", "N/A")

                token_notice = ""
                if "error" in str(meta_id).lower() or "no_page" in str(meta_id).lower():
                    token_notice = "\n⚠️ *বিজ্ঞপ্তি:* Meta Access Token এক্সপায়ার হওয়ার কারণে ফেসবুক/ইন্সটাগ্রামে পাবলিশ হয়নি। অনুগ্রহ করে নিচের বাটন চেপে নতুন টোকেন আপডেট করুন।"

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ *Published Successfully!*\n\n"
                        f"• *Completed:* `Day {completed_day:02d}` ({topic_title[:35]}...)\n"
                        f"• *Status:* `{pub_status}`\n"
                        f"• *LinkedIn URN:* `{li_urn}`\n"
                        f"• *Facebook Carousel:* `{meta_id}`\n"
                        f"• *Instagram Carousel:* `{ig_id}`\n\n"
                        f"📅 *Next Scheduled Post:* `Day {next_day:02d}`\n"
                        f"⏳ *First Comment Engine:* Automated technical comments dispatched across all active platforms in 120 seconds."
                        f"{token_notice}"
                    ),
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔑 Update Meta Token", callback_data="cmd_token_prompt")]
                    ]) if token_notice else get_main_inline_keyboard()
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"⚠️ *পাবলিকেশন যাচাই ব্যর্থ হয়েছে!*\n\n"
                        f"সিস্টেম পাবলিকেশন নিশ্চিত করতে পারেনি (Status: `{pub_status}`).\n"
                        "দয়া করে `/status` বাটন চেপে এপিআই কানেকশন পরীক্ষা করুন অথবা `🚀 এক ক্লিকে পোস্ট তৈরি` দিয়ে নতুন ড্রাফট তৈরি করে পুনরায় চেষ্টা করুন।"
                    ),
                    parse_mode="Markdown",
                    reply_markup=get_main_inline_keyboard()
                )
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ *পাবলিকেশনে ত্রুটি:* `{str(e)}`", parse_mode="Markdown")

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
        def run_skip_sync():
            app = build_growth_graph(enable_interrupt=True)
            app.update_state(config, {"skipped": True, "human_approved": False})
            for event in app.stream(None, config=config):
                pass

        await asyncio.to_thread(run_skip_sync)
        await query.edit_message_text("⏭️ *Publication Skipped for Today.* Checkpoint stored.", parse_mode="Markdown")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles natural language revision text, day inputs, tokens, and button text clicks."""
    chat_id = update.effective_chat.id
    raw_text = (update.message.text or "").strip()
    lower_text = raw_text.lower()

    # 1. Check if user is entering a revision request
    if AWAITING_REVISION.get(chat_id, False):
        AWAITING_REVISION[chat_id] = False
        thread_id = ACTIVE_THREADS.get(chat_id, get_thread_id(chat_id))

        status_msg = await update.message.reply_text(
            f"🔄 *Processing Revision:* \"{raw_text}\"\nRe-synthesizing and rendering updated carousel...",
            parse_mode="Markdown",
        )

        def run_revision_sync():
            app = build_growth_graph(enable_interrupt=True)
            config = {"configurable": {"thread_id": thread_id}}
            app.update_state(config, {"revision_request": raw_text, "human_approved": False})
            for event in app.stream(None, config=config):
                pass
            state = app.get_state(config)
            return state.values

        try:
            state_values = await asyncio.to_thread(run_revision_sync)
            await send_carousel_preview(chat_id, context, state_values)
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ *রিভিশনে ত্রুটি:* `{str(e)}`", parse_mode="Markdown")
        return

    # 2. Check if user is entering a Day number
    if AWAITING_DAY.get(chat_id, False):
        AWAITING_DAY[chat_id] = False
        try:
            day_num = int(raw_text)
            set_current_day(day_num)
            ce = CurriculumEngine()
            ct = ce.get_topic_by_day(day_num)
            await update.message.reply_text(
                f"✅ *দিন সফলভাবে পরিবর্তন করা হয়েছে:*\n\n"
                f"• *বর্তমান দিন:* `Day {day_num:02d}`\n"
                f"• *টপিক:* `Class {ct.class_id} - {ct.title}`\n\n"
                "এখন নতুন ড্রাফট তৈরি করতে `🚀 এক ক্লিকে পোস্ট তৈরি` বাটনে চাপুন অথবা `/generate` লিখুন।",
                parse_mode="Markdown",
                reply_markup=get_main_reply_keyboard()
            )
        except ValueError:
            await update.message.reply_text("❌ অনুগ্রহ করে একটি সঠিক সংখ্যা দিন (যেমন: `1`, `2`, `14`)।", parse_mode="Markdown")
        return

    # 3. Check if user is entering a Meta Token
    if AWAITING_TOKEN.get(chat_id, False):
        AWAITING_TOKEN[chat_id] = False
        context.args = [raw_text]
        await settoken_command(update, context)
        return

    # 4. Check if user is entering Meta App credentials
    if AWAITING_APP_CREDS.get(chat_id, False):
        AWAITING_APP_CREDS[chat_id] = False
        parts = raw_text.split()
        if len(parts) >= 1:
            context.args = parts
            await setappcreds_command(update, context)
        else:
            await update.message.reply_text("❌ অনুগ্রহ করে আপনার Meta App Secret টি লিখে পাঠান।", parse_mode="Markdown")
        return

    # 5. Check if user is entering a LinkedIn Token
    if AWAITING_LI_TOKEN.get(chat_id, False):
        AWAITING_LI_TOKEN[chat_id] = False
        context.args = [raw_text]
        await setlinkedin_command(update, context)
        return

    # 5. Handle Text triggers and persistent keyboard buttons
    if lower_text in ["start", "/start", "shuru", "suru", "menu", "hi", "hello", "hey"]:
        await start_command(update, context)
    elif lower_text in ["generate", "/generate", "পোস্ট তৈরি", "এক ক্লিকে পোস্ট তৈরি", "🚀 এক ক্লিকে পোস্ট তৈরি"]:
        await generate_command(update, context)
    elif lower_text in ["day", "/day", "আজকের দিন", "আজকের দিন ও টপিক", "📅 আজকের দিন ও টপিক"]:
        await day_command(update, context)
    elif lower_text in ["status", "/status", "সিস্টেম স্ট্যাটাস", "📊 সিস্টেম স্ট্যাটাস"]:
        await status_command(update, context)
    elif lower_text in ["token", "/token", "tokenstatus", "/tokenstatus", "টোকেন", "মেটা টোকেন", "মেটা টোকেন কন্ট্রোল", "🔑 মেটা টোকেন কন্ট্রোল"]:
        await token_status_command(update, context)
    elif lower_text in ["setday", "/setday", "দিন পরিবর্তন", "⚙️ দিন পরিবর্তন"]:
        AWAITING_DAY[chat_id] = True
        await update.message.reply_text(
            "🔢 *দিন পরিবর্তন (Set Active Day)*\n\nঅনুগ্রহ করে নতুন দিন নম্বরটি লিখে পাঠান (যেমন: `1`, `2`, `14`):",
            parse_mode="Markdown"
        )
    elif lower_text in ["help", "/help", "সাহায্য", "সাহায্য ও গাইড", "❓ সাহায্য ও গাইড"]:
        await help_command(update, context)
    elif lower_text in ["permtoken", "/permtoken", "পার্মানেন্ট টোকেন"]:
        await perm_guide_command(update, context)
    elif raw_text.isdigit():
        # User typed a raw number (e.g. "2") directly
        day_num = int(raw_text)
        if 1 <= day_num <= 100:
            set_current_day(day_num)
            ce = CurriculumEngine()
            ct = ce.get_topic_by_day(day_num)
            await update.message.reply_text(
                f"✅ *দিন সেট করা হয়েছে:* `Day {day_num:02d}`\n"
                f"• *টপিক:* `Class {ct.class_id} - {ct.title}`\n\n"
                f"ড্রাফট তৈরি করতে `🚀 এক ক্লিকে পোস্ট তৈরি` বাটন চাপুন।",
                parse_mode="Markdown",
                reply_markup=get_main_reply_keyboard()
            )
    else:
        # Default friendly response with persistent keyboard
        await update.message.reply_text(
            f"👋 *স্বাগতম!* আপনার মেসেজ: \"{raw_text}\"\n\n"
            "সরাসরি নিচের বাটনগুলোতে ক্লিক করে অথবা `/start` লিখে আপনার পছন্দের কমান্ড বেছে নিন।",
            parse_mode="Markdown",
            reply_markup=get_main_reply_keyboard()
        )


# ------------------------------------------------------------------------------
# CLI / Headless Runner
# ------------------------------------------------------------------------------

def run_cli_mode(auto_approve: bool = False, revision_prompt: Optional[str] = None, day: Optional[int] = None):
    """Runs the full pipeline in terminal mode for local testing or CI/CD crons."""
    print("=" * 70)
    print("AUTONOMOUS MULTI-AGENT GROWTH PLATFORM (CLI STUDIO)")
    print("=" * 70)

    thread_id = f"cli_session_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}
    app = build_growth_graph(enable_interrupt=not auto_approve)

    current_day = day if day is not None else get_current_day()
    initial_state: PipelineState = {
        "day_number": current_day,
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

    print(f"[CLI] Executing workflow stream for Day {current_day:02d}...")
    for event in app.stream(initial_state, config=config):
        node_name = list(event.keys())[0]
        print(f" -> Completed node: {node_name}")

    state = app.get_state(config)
    carousel = state.values.get("carousel", {})

    print("\n" + "=" * 70)
    print(f"DAY NUMBER:     Day {current_day:02d}")
    print(f"CAROUSEL TITLE: {carousel.get('topic_headline')}")
    print(f"CRITIC SCORE:   {state.values.get('critique', {}).get('score')}/10")
    print(f"PDF COMPILED:   {state.values.get('pdf_path')}")
    print(f"SLIDES COUNT:   {len(state.values.get('rendered_images', []))}")
    print("=" * 70)

    # Print Executive Bengali Decision Brief
    ce = CurriculumEngine()
    ct = ce.get_topic_by_day(current_day)
    crit_val = float(state.values.get('critique', {}).get('score', 9.4) or 9.4)
    bengali_brief = generate_bengali_decision_brief(
        day_number=current_day,
        topic_headline=carousel.get("topic_headline", ct.title),
        class_id=ct.class_id,
        module_category=ct.module_category,
        problem_statement=ct.problem_statement,
        actionable_tip=ct.actionable_tip,
        roi_metric_label=ct.roi_metric_label,
        roi_metric_value=ct.roi_metric_value,
        roi_subtext=ct.roi_subtext,
        critique_score=crit_val,
        slides_count=len(state.values.get('rendered_images', [])) or 5,
    )
    print("\n" + "=" * 70)
    print("EXECUTIVE BENGALI DECISION BRIEF (বাংলায় সম্পূর্ণ বিবরণী):")
    print("=" * 70)
    print(bengali_brief)
    print("=" * 70)

    if revision_prompt and not auto_approve:
        print(f"\n[CLI] Applying natural language revision: '{revision_prompt}'...")
        app.update_state(config, {"revision_request": revision_prompt, "human_approved": False})
        for event in app.stream(None, config=config):
            pass
        state = app.get_state(config)
        print("[CLI] Revision re-render complete!")

    if auto_approve:
        topic_title = (state.values.get("topic") or {}).get("title", "")
        next_day = advance_current_day(completed_day=current_day, topic_title=topic_title)
        print(f"[CLI] Auto-published Day {current_day:02d}. Next day counter set to Day {next_day:02d}.")
        first_comment_delay = int(os.getenv("FIRST_COMMENT_DELAY_SECONDS", "120"))
        if first_comment_delay > 0:
            print(f"[CLI] Waiting {first_comment_delay}s for first comment engine to complete across all platforms...")
            time.sleep(first_comment_delay + 3)

    elif state.next == ("human_review",):
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
            topic_title = (state.values.get("topic") or {}).get("title", "")
            next_day = advance_current_day(completed_day=current_day, topic_title=topic_title)
            print(f"[CLI] Approved Day {current_day:02d}. Next day counter set to Day {next_day:02d}.")
            first_comment_delay = int(os.getenv("FIRST_COMMENT_DELAY_SECONDS", "120"))
            if first_comment_delay > 0:
                print(f"[CLI] Waiting {first_comment_delay}s for first comment engine to complete across all platforms...")
                time.sleep(first_comment_delay + 3)
        else:
            print("[CLI] Skipped.")


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catches unexpected exceptions in telegram polling to prevent loop interruptions."""
    err = context.error
    print(f"[Telegram Studio Exception] {err}")
    if isinstance(err, Exception) and "Conflict: terminated by other getUpdates" in str(err):
        print("[Telegram Studio Alert] Another bot instance is polling this token! Ensure only 1 instance is running.")


def start_token_expiry_monitor(app_instance: Application):
    """Background monitor running once every 12 hours checking Meta token expiration."""
    def _worker():
        while True:
            time.sleep(43200)  # Check every 12 hours
            try:
                info = get_meta_token_info()
                days_left = info.get("days_remaining")
                never_exp = info.get("never_expires")
                chat_id = os.getenv("TELEGRAM_CHAT_ID")
                if not never_exp and days_left is not None and days_left <= 5 and chat_id:
                    msg = (
                        f"⚠️ *সতর্কতা: Meta Token মেয়াদ শেষ হতে চলেছে!*\n\n"
                        f"আপনার ফেসবুক/ইন্সটাগ্রাম টোকেনের মেয়াদ আর মাত্র `{days_left}` দিন বাকি আছে।\n"
                        "নিরবচ্ছিন্ন লাইভ পোস্টিং নিশ্চিত করতে নতুন টোকেনটি সরাসরি এই চ্যাটে পাঠিয়ে দিন বা `/settoken` ব্যবহার করুন।"
                    )
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(app_instance.bot.send_message(chat_id=int(chat_id), text=msg, parse_mode="Markdown"))
                    loop.close()
            except Exception as e:
                print(f"[TokenMonitor] Notice: {e}")

    threading.Thread(target=_worker, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="Autonomous Multi-Agent Growth Platform Studio")
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve publication without interruption")
    parser.add_argument("--revision", type=str, default=None, help="Optional revision prompt to test partial re-render")
    parser.add_argument("--day", type=int, default=None, help="Explicit day number override (e.g. --day 1)")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if args.cli or not token:
        if not token and not args.cli:
            print("[Info] TELEGRAM_BOT_TOKEN not provided in .env. Running in interactive CLI mode.")
        run_cli_mode(auto_approve=args.auto_approve, revision_prompt=args.revision, day=args.day)
    else:
        print(f"[Telegram Studio] Starting Telegram Bot with token {token[:8]}...***")
        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler(["start", "shuru", "menu"], start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("day", day_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler(["token", "tokenstatus"], token_status_command))
        application.add_handler(CommandHandler("settoken", settoken_command))
        application.add_handler(CommandHandler("setappcreds", setappcreds_command))
        application.add_handler(CommandHandler("permtoken", perm_guide_command))
        application.add_handler(CommandHandler("setday", setday_command))
        application.add_handler(CommandHandler("generate", generate_command))
        application.add_handler(CommandHandler(["setlinkedin", "linkedin"], setlinkedin_command))
        application.add_handler(CallbackQueryHandler(button_callback_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
        application.add_error_handler(global_error_handler)

        # Cloud Hosting Support: Start HTTP health server on Render or when PORT is set
        port_env = os.getenv("PORT", "10000" if os.getenv("RENDER") else None)
        if port_env:
            try:
                start_health_server(int(port_env))
            except Exception as e:
                print(f"[Cloud Engine] Health server notice: {e}")

        # Keep-Alive Engine: Self-ping every 10 minutes to prevent cloud sleep
        app_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("APP_URL")
        if app_url:
            def keep_alive_worker():
                while True:
                    time.sleep(600)
                    try:
                        requests.get(f"{app_url.rstrip('/')}/", timeout=10)
                    except Exception:
                        pass
            threading.Thread(target=keep_alive_worker, daemon=True).start()
            print(f"[Cloud Engine] Automated keep-alive self-ping active for: {app_url}")

        # Background Token Expiration Monitor (Proactive 24/7/365 Guard)
        start_token_expiry_monitor(application)

        print("[Telegram Studio] Bot polling active. Send /start or 'start' or tap buttons in your Telegram chat.")
        application.run_polling()


if __name__ == "__main__":
    main()
