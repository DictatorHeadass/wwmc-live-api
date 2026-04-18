import time
import urllib.request
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Cache ─────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 30  # seconds

def check_live(username: str) -> bool:
    try:
        url = f'https://www.tiktok.com/@{username}/live'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        # When live, TikTok embeds active room data containing "liveRoomInfo"
        # When not live the key is absent or room status is not 4 (ongoing)
        return '"liveRoomInfo"' in html and '"status":4' in html
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

# ── Routes ────────────────────────────────────────────────
@app.route('/api/live')
def live():
    raw       = request.args.get('usernames', '')
    usernames = [u.strip().lstrip('@') for u in raw.split(',') if u.strip()]
    results   = {u: get_status(u) for u in usernames}
    resp      = jsonify(results)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/debug')
def debug():
    username = request.args.get('username', 'yurialpha7_')
    out = {}
    try:
        url = f'https://www.tiktok.com/@{username}/live'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        # Search for relevant substrings and return 120-char snippets around each
        # Find liveRoom value — show what comes right after the key
        idx = html.find('"liveRoom":')
        out['liveRoom_snippet'] = html[idx:idx+120] if idx != -1 else None
        out['has_liveRoom_object'] = '"liveRoom":{"' in html
        out['html_length'] = len(html)
    except Exception as e:
        out['error'] = str(e)
    resp = jsonify(out)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
