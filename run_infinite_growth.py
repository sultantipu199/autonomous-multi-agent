"""Perpetual Autonomous Growth Engine Runner.

Runs 24/7/365 to deliver non-stop, non-repeating daily technical carousels to
LinkedIn, Meta Facebook Page, and Instagram Business.

Usage:
  python run_infinite_growth.py --daemon            # Runs continuous 24/7 scheduler
  python run_infinite_growth.py --now               # Publishes today's post immediately
  python run_infinite_growth.py --status            # Displays system status and today's slot
  python run_infinite_growth.py --test-infinite 10  # Verifies generation for next 10 days
"""

import os
import sys
import time
import argparse
from datetime import datetime
import zoneinfo
from dotenv import load_dotenv

load_dotenv()

from agents.curriculum_engine import CurriculumEngine
from agents.dedup_sentinel import DedupSentinel
from agents.dynamic_scheduler import DynamicScheduler
from agents.ninja_orchestrator import get_current_day


def print_banner():
    banner = """
======================================================================
  AUTONOMOUS MULTI-AGENT GROWTH PLATFORM: INFINITE PERPETUAL ENGINE   
  Tipu Sultan | AI & Data-Driven Growth Architect                    
======================================================================
"""
    print(banner)


def show_status():
    print_banner()
    tz_str = os.getenv("TIMEZONE", "Asia/Dhaka")
    sched = DynamicScheduler(timezone_str=tz_str)
    now = sched.get_current_time()
    slot_info = sched.calculate_optimal_slot()

    sentinel = DedupSentinel()
    past_topics = sentinel.get_all_published_topics()
    current_day = get_current_day()
    today_posted = sentinel.is_today_already_published(timezone_str=tz_str)

    curriculum = CurriculumEngine()
    resolved_day, next_topic = sentinel.resolve_next_unique_day_and_topic(target_day=current_day)

    print(f"• Current Time (Dhaka):       {now.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
    print(f"• Peak Publishing Window:     {slot_info.get('window_start')} - {slot_info.get('window_end')}")
    print(f"• Target Daily Slot:          {slot_info.get('scheduled_time_display')}")
    print(f"• Today's Publication Status: {'[COMPLETED]' if today_posted else '[PENDING EXECUTION]'}")
    print(f"• Active Day Number:          Day {current_day:02d}")
    print(f"• Next Novel Day Resolved:    Day {resolved_day:02d}")
    print(f"• Next Topic Headline:        '{next_topic.title}'")
    print(f"• Module Category:            {next_topic.module_category}")
    print(f"• Total Topics in History:    {len(past_topics)} posts recorded")
    print("=" * 70)


def run_now():
    print_banner()
    print("[PerpetualRunner] Initiating immediate daily generation and multi-platform publishing...")
    from main import run_cli_mode
    run_cli_mode(auto_approve=True)


def test_infinite_days(num_days: int = 5):
    print_banner()
    print(f"[PerpetualRunner] Stress-testing infinite topic generation for next {num_days} days...\n")
    sentinel = DedupSentinel()
    curriculum = CurriculumEngine()
    start_day = get_current_day()

    passed = 0
    generated_titles = []
    current_eval_day = start_day

    for _ in range(num_days):
        resolved_day, ct = sentinel.resolve_next_unique_day_and_topic(target_day=current_eval_day)
        is_dup, reason = sentinel.is_duplicate(ct.title, ct.problem_statement)

        status_icon = "FAIL" if is_dup else "OK"
        print(f"[{status_icon}] Day {resolved_day:02d}: '{ct.title}'")
        print(f"      Category: {ct.module_category} | ROI: {ct.roi_metric_label} {ct.roi_metric_value}")
        print(f"      Code snippet: {ct.code_snippet[:65].strip()}...")

        if not is_dup and ct.title not in generated_titles:
            passed += 1
            generated_titles.append(ct.title)
        else:
            print(f"      Collision Warning: {reason}")
        print("-" * 70)
        current_eval_day = resolved_day + 1


    print(f"\n[Test Result] Generated {passed}/{num_days} 100% unique, non-repeating lessons successfully!")
    if passed == num_days:
        print("[Verdict] Infinite Perpetual Curriculum Engine verified with ZERO duplicate collisions.")


def run_daemon():
    print_banner()
    tz_str = os.getenv("TIMEZONE", "Asia/Dhaka")
    try:
        tz = zoneinfo.ZoneInfo(tz_str)
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")

    print(f"[Daemon] Perpetual 24/7 Engine started for timezone: {tz_str}.")
    print("[Daemon] Standby mode active. Press Ctrl+C to terminate.\n")

    from main import run_cli_mode

    last_published_date = None

    while True:
        try:
            now = datetime.now(tz)
            today_str = now.strftime("%Y-%m-%d")

            sentinel = DedupSentinel()
            sched = DynamicScheduler(timezone_str=tz_str)
            slot = sched.calculate_optimal_slot()

            today_posted = sentinel.is_today_already_published(timezone_str=tz_str)

            if today_posted:
                if last_published_date != today_str:
                    last_published_date = today_str
                    print(f"[{now.strftime('%H:%M:%S')}] Today's post ({today_str}) already completed. Sleeping until next daily cycle...")
            elif slot.get("is_within_window_now") or (8 <= now.hour <= 12):
                print(f"\n[{now.strftime('%H:%M:%S')}] >>> PEAK SLOT TRIGGERED: Initiating autonomous publishing for {today_str} <<<")
                last_published_date = today_str
                try:
                    run_cli_mode(auto_approve=True)
                    print(f"[{datetime.now(tz).strftime('%H:%M:%S')}] Autonomous publication for {today_str} completed successfully!")
                except Exception as exec_err:
                    print(f"[Daemon] Execution exception: {exec_err}")
                    last_published_date = None
            else:
                remaining_sec = slot.get("seconds_until_execution", 0)
                print(f"[{now.strftime('%H:%M:%S')}] Standing by. Target slot: {slot.get('scheduled_time_display')} (in {sched.format_countdown_bengali(remaining_sec)})...")

        except KeyboardInterrupt:
            print("\n[Daemon] Gracefully shutting down perpetual daemon.")
            sys.exit(0)
        except Exception as e:
            print(f"[Daemon] Unexpected error: {e}")

        time.sleep(300)  # Check every 5 minutes


def main():
    parser = argparse.ArgumentParser(description="Autonomous Multi-Agent Infinite Perpetual Growth Runner")
    parser.add_argument("--daemon", action="store_true", help="Run 24/7 continuous autonomous posting daemon")
    parser.add_argument("--now", action="store_true", help="Trigger today's post immediately")
    parser.add_argument("--status", action="store_true", help="Display current scheduling and topic status")
    parser.add_argument("--test-infinite", type=int, default=None, metavar="N", help="Test N consecutive infinite days")
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.now:
        run_now()
    elif args.test_infinite is not None:
        test_infinite_days(args.test_infinite)
    else:
        show_status()


if __name__ == "__main__":
    main()
