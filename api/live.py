from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import asyncio
import time

# ── Cache ────────────────────────────────────────────────
# Stores { username: (is_live: bool, timestamp: float) }
# Results are reused for 30 seconds to avoid hammering TikTok
_cache: dict = {}
CACHE_TTL = 30

async def _check(username: str) -> bool:
    try:
        from TikTokLive import TikTokLiveClient
        client = TikTokLiveClient(unique_id=username)
        return await client.is_live(username)
    except Exception:
        return False

def get_live_status(username: str) -> bool:
    now = time.time()
    if username in _cache:
        result, ts = _cache[username]
        if now - ts < CACHE_TTL:
            return result
    result = asyncio.run(_check(username))
    _cache[username] = (result, now)
    return result

# ── Vercel handler ────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        raw = params.get('usernames', [''])[0]
        usernames = [u.strip().lstrip('@') for u in raw.split(',') if u.strip()]

        results = {u: get_live_status(u) for u in usernames}

        body = json.dumps(results).encode()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
