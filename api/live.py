import asyncio
import time
from flask import Flask, request, jsonify
from TikTokLive import TikTokLiveClient

app = Flask(__name__)

# ── Simple in-memory cache ────────────────────────────────
_cache: dict = {}
CACHE_TTL = 30  # seconds

async def _check(username: str) -> bool:
    try:
        client = TikTokLiveClient(unique_id=username)
        return await client.is_live(username)
    except Exception:
        return False

def get_status(username: str) -> bool:
    now = time.time()
    if username in _cache:
        result, ts = _cache[username]
        if now - ts < CACHE_TTL:
            return result
    result = asyncio.run(_check(username))
    _cache[username] = (result, now)
    return result

# ── Route ─────────────────────────────────────────────────
@app.route('/api/live')
def live():
    raw      = request.args.get('usernames', '')
    usernames = [u.strip().lstrip('@') for u in raw.split(',') if u.strip()]
    results  = {u: get_status(u) for u in usernames}
    resp     = jsonify(results)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
