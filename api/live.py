import time
import json
import urllib.request
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Cache ─────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 30  # seconds

def check_live(username: str) -> bool:
    try:
        url = (
            'https://webcast.tiktok.com/webcast/room/check_alive/'
            f'?aid=1988&uniqueId={username}'
        )
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
        })
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
        return bool(data.get('data', {}).get('alive', False))
    except Exception:
        return False

def get_status(username: str) -> bool:
    now = time.time()
    if username in _cache:
        result, ts = _cache[username]
        if now - ts < CACHE_TTL:
            return result
    result = check_live(username)
    _cache[username] = (result, now)
    return result

# ── Route ─────────────────────────────────────────────────
@app.route('/api/live')
def live():
    raw       = request.args.get('usernames', '')
    usernames = [u.strip().lstrip('@') for u in raw.split(',') if u.strip()]
    results   = {u: get_status(u) for u in usernames}
    resp      = jsonify(results)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
