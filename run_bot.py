"""Telegram Bot Supervisor and Resilient Auto-Restart Watchdog.

Keeps the Autonomous Multi-Agent Telegram Studio running continuously 24/7.
Logs output to `data/bot.log` and automatically recovers from transient network drops.
"""

import os
import sys
import time
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

LOG_FILE = os.path.join("data", "bot.log")
os.makedirs("data", exist_ok=True)


def main():
    print("=" * 65)
    print("AUTONOMOUS MULTI-AGENT TELEGRAM BOT SUPERVISOR")
    print(f"Logging to: {LOG_FILE}")
    print("=" * 65)

    backoff = 2
    while True:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log_f:
                log_f.write(f"\n--- Bot process started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                log_f.flush()

                # Launch main.py with unbuffered stdout
                cmd = [sys.executable, "-u", "main.py"]
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=log_f,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                )

                print(f"[Supervisor] Bot launched with PID {process.pid}.")
                ret_code = process.wait()
                log_f.write(f"\n--- Bot process exited with code {ret_code} at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                log_f.flush()

            print(f"[Supervisor] Bot process terminated (code {ret_code}). Restarting in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 30)

        except KeyboardInterrupt:
            print("\n[Supervisor] Stopping bot watchdog on user request.")
            try:
                process.terminate()
            except Exception:
                pass
            break
        except Exception as e:
            print(f"[Supervisor] Unexpected exception: {e}. Retrying in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
