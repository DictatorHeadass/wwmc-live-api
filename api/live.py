import re
import time
import urllib.request
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# ── Cache ─────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 30  # seconds

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_live_page(username: str) -> str:
    url = f'https://www.tiktok.com/@{username}/live'
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def check_live(username: str) -> bool:
    try:
        html = fetch_live_page(username)
        # liveRoom.status: 2 = streaming now, 4 = ended (cached from last stream)
        idx = html.find('"liveRoom":{')
        if idx == -1:
            return False
        return '"status":2' in html[idx:idx+600]
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

@app.route('/api/avatar')
def avatar():
    username = request.args.get('username', '').strip().lstrip('@')
    if not username:
        return ('missing username', 400)
    try:
        html = fetch_live_page(username)
        # Extract avatar — avatarLarger is always present in user data
        m = re.search(r'"avatarLarger":"(https://[^"]+)"', html)
        if not m:
            return ('avatar not found', 404)
        avatar_url = m.group(1).replace('\\/', '/').replace('\\u002F', '/')
        # Proxy the image so the browser can cache it for 12 hours
        img_req = urllib.request.Request(avatar_url, headers={
            **HEADERS, 'Referer': 'https://www.tiktok.com/'
        })
        with urllib.request.urlopen(img_req, timeout=10) as img_resp:
            img_data  = img_resp.read()
            ctype     = img_resp.headers.get('Content-Type', 'image/webp')
        resp = Response(img_data, content_type=ctype)
        resp.headers['Cache-Control']             = 'public, max-age=43200'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception as e:
        return (str(e), 500)

@app.route('/api/debug')
def debug():
    username = request.args.get('username', 'yurialpha7_')
    out = {}
    try:
        html = fetch_live_page(username)
        idx  = html.find('"liveRoom":{')
        out['liveRoom_object'] = html[idx:idx+600] if idx != -1 else None
        m = re.search(r'"avatarLarger":"(https://[^"]+)"', html)
        out['avatarLarger'] = m.group(1) if m else None
        out['html_length']  = len(html)
    except Exception as e:
        out['error'] = str(e)
    resp = jsonify(out)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
