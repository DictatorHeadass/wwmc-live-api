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
    # Try check_alive endpoint
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
        with urllib.request.urlopen(req, timeout=6) as r:
            out['check_alive'] = {'status': r.status, 'body': r.read().decode('utf-8', errors='replace')}
    except Exception as e:
        out['check_alive'] = {'error': str(e)}
    # Try profile page redirect check
    try:
        url2 = f'https://www.tiktok.com/@{username}/live'
        req2 = urllib.request.Request(url2, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
        })
        with urllib.request.urlopen(req2, timeout=10) as r:
            out['live_page'] = {'final_url': r.geturl(), 'status': r.status}
    except Exception as e:
        out['live_page'] = {'error': str(e)}
    resp = jsonify(out)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
