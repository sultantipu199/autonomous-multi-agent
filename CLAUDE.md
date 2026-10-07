# CLAUDE.md

## Commands
- Run CLI headless: `python main.py --cli --auto-approve`
- Run Interactive Telegram Bot: `python main.py`
- Run Bot Watchdog Supervisor: `python run_bot.py`
- Run Test Suite: `python -m unittest tests/test_system_suite.py`

## Instagram Publishing Guidelines
- Instagram Graph API requires valid publicly accessible HTTPS images.
- Always use Meta's First-Party Page Photo upload (`/{page_id}/photos?published=false`) to host slide images directly on Meta's internal CDN (`scontent.*.fbcdn.net`).
- Do not use third-party temporary upload services like tmpfiles or Catbox in production pipelines as they get blocked by Cloudflare or return HTML error pages to Meta's crawler.
- Ensure all carousel slides are 1080x1080 (1:1 aspect ratio).
