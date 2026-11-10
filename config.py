"""URL ➜ HTML API settings. Hardcoded on purpose (private deployment)."""
import os

# Every client (your Telegram bot, other apps) sends one of these in the
# X-API-Key header. Add more keys to give other clients their own key.
API_KEYS = ["d9RGoLP4ZOi7_waN7OsxT5xeYDztwmtR9lc8bO83pwI"]

PORT = int(os.environ.get("PORT", 8080))

# ── job engine ──
MAX_RUNNING_JOBS = 3        # crawls/zips running at once (RAM protection)
MAX_QUEUED_JOBS = 100       # extra jobs wait; above this the API answers 429
JOB_TTL_SECONDS = 30 * 60   # finished ZIPs are deleted after this

# ── crawler limits ──
MAX_SITE_PAGES = 150
MAX_SITE_DEPTH = 5
MAX_SITE_ASSETS = 1200
MAX_ASSETS_SINGLE = 500
MAX_PAGE_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_ASSET_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_DOWNLOAD_BYTES = 120 * 1024 * 1024   # stop collecting assets after this
PAGE_CONCURRENCY = 6
ASSET_CONCURRENCY = 10
MAX_SAFE_REDIRECTS = 5
