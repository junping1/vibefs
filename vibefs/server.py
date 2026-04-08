import hmac
import json as json_mod
import mimetypes
import os
import time
import urllib.parse
import threading

import bottle

from .config import load_config, get_owner_key
from .constants import (
    DEFAULT_TTL, DIR_DEFAULT_TTL, MAX_RENDER_SIZE, TIME_FORMAT,
    STATUS_VALID, STATUS_EXPIRED, STATUS_NOT_FOUND, STATUS_ACTIVE,
)
from .db import (
    get_db, lookup_authorization, lookup_dir_authorization,
    lookup_git_authorization, get_git_commit_info, list_all_authorizations,
)
from .renderers import get_renderer
from .templates import render_template, _dual_pygments_css
from .utils import (
    _display_path, _html_escape, _js_safe_json, _js_string_escape,
    is_safe_subpath, walk_directory, get_file_type,
)

app = bottle.Bottle()


# --- Rate limiting ---

_rate_limits = {}
_rate_lock = threading.Lock()
_rate_last_cleanup = time.time()
RATE_LIMIT = 60
RATE_WINDOW = 60
RATE_CLEANUP_INTERVAL = 300  # purge stale IPs every 5 minutes


def _get_client_ip():
    """Get the real client IP, preferring CF-Connecting-IP (Cloudflare),
    then the last entry in X-Forwarded-For (closest trusted proxy added it),
    then falling back to remote_addr."""
    cf_ip = bottle.request.environ.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip.strip()
    xff = bottle.request.environ.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # Last entry is the one added by the closest trusted reverse proxy
        return xff.split(',')[-1].strip()
    return bottle.request.remote_addr


@app.hook('before_request')
def rate_limit():
    global _rate_last_cleanup
    ip = _get_client_ip()
    now = time.time()
    with _rate_lock:
        # Periodic cleanup of stale IPs
        if now - _rate_last_cleanup > RATE_CLEANUP_INTERVAL:
            stale = [k for k, v in _rate_limits.items() if not v or v[-1] < now - RATE_WINDOW]
            for k in stale:
                del _rate_limits[k]
            _rate_last_cleanup = now

        entries = _rate_limits.get(ip)
        if entries is not None:
            _rate_limits[ip] = entries = [t for t in entries if now - t < RATE_WINDOW]
        else:
            entries = []
            _rate_limits[ip] = entries
        if len(entries) >= RATE_LIMIT:
            bottle.abort(429, 'Rate limit exceeded')
        entries.append(now)


# --- Anti-crawler headers ---

@app.hook('after_request')
def add_security_headers():
    bottle.response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'
    bottle.response.headers['Referrer-Policy'] = 'no-referrer'
    bottle.response.headers['X-Content-Type-Options'] = 'nosniff'


@app.route('/robots.txt')
def robots():
    bottle.response.content_type = 'text/plain'
    return 'User-agent: *\nDisallow: /\n'


# --- Auth helpers ---

def _check_expired_auth(password):
    """Check if user has a valid auth cookie. Returns True if verified."""
    return bottle.request.get_cookie('vibefs_auth', secret=password) == 'verified'


def _check_owner_auth():
    """Check if the request has a valid owner cookie (30-day)."""
    owner_key = get_owner_key()
    return bottle.request.get_cookie('vibefs_owner', secret=owner_key) == 'owner'


_ALLOWED_TABLES = {'authorizations', 'git_authorizations', 'dir_authorizations'}


def _extend_expiry(table, token, ttl):
    """Extend a token's expiry. Table name must be in the allowlist."""
    if table not in _ALLOWED_TABLES:
        raise ValueError(f'Invalid table: {table}')
    db = get_db()
    db.execute(f'UPDATE {table} SET expires_at = ? WHERE token = ?', (time.time() + ttl, token))
    db.commit()
    db.close()


def _handle_expired(row, name_field, token, table='authorizations'):
    """Handle expired authorization. Returns response HTML or None if owner-authed."""
    cfg = load_config()
    ttl = cfg.get('dir_default_ttl', DIR_DEFAULT_TTL) if table == 'dir_authorizations' else cfg.get('file_ttl', DEFAULT_TTL)

    # Owner cookie bypasses expiry
    if _check_owner_auth():
        _extend_expiry(table, token, ttl)
        return None

    # Regular auth cookie (for backward compat with password config)
    password = cfg.get('password')
    if password and _check_expired_auth(password):
        _extend_expiry(table, token, ttl)
        return None

    verify_url = f'/verify?next={bottle.request.path}' if password else ''
    return render_template('expired.html', filename=row[name_field], verify_url=verify_url)


# --- Verify (existing) ---

@app.route('/verify')
def verify_page():
    next_url = bottle.request.query.get('next', '/')
    cfg = load_config()
    password = cfg.get('password')
    if not password:
        bottle.abort(403, 'No password configured')
    if _check_expired_auth(password):
        bottle.redirect(next_url)
    return render_template('verify.html', next_url=next_url, error='')


@app.post('/verify')
def verify_submit():
    next_url = bottle.request.forms.get('next', '/')
    if not next_url.startswith('/'):
        next_url = '/'
    cfg = load_config()
    password = cfg.get('password')
    if not password:
        bottle.abort(403, 'No password configured')

    submitted = bottle.request.forms.get('password', '')
    if hmac.compare_digest(submitted, password):
        bottle.response.set_cookie('vibefs_auth', 'verified', secret=password, path='/', max_age=86400, httponly=True, samesite='Lax')
        bottle.redirect(next_url)
    else:
        return render_template('verify.html', next_url=next_url, error='Incorrect password')


# --- Owner auth (key-based) ---

@app.route('/owner/auth')
def owner_auth():
    """Authenticate owner via ?key= param, set long-lived cookie."""
    key = bottle.request.query.get('key', '')
    next_url = bottle.request.query.get('next', '/dashboard')
    if not next_url.startswith('/'):
        next_url = '/dashboard'

    owner_key = get_owner_key()
    if not key or not hmac.compare_digest(key, owner_key):
        bottle.abort(403, 'Invalid key')

    bottle.response.set_cookie('vibefs_owner', 'owner', secret=owner_key, path='/', max_age=30 * 86400, httponly=True, samesite='Lax')
    bottle.redirect(next_url)


# --- Dashboard ---

@app.route('/dashboard')
def dashboard():
    # Allow ?key= param to authenticate inline
    key = bottle.request.query.get('key', '')
    if key:
        owner_key = get_owner_key()
        if hmac.compare_digest(key, owner_key):
            bottle.response.set_cookie('vibefs_owner', 'owner', secret=owner_key, path='/', max_age=30 * 86400, httponly=True, samesite='Lax')
        else:
            bottle.abort(403, 'Invalid key')
    elif not _check_owner_auth():
        bottle.abort(403, 'Access denied')

    shares = list_all_authorizations()
    for s in shares:
        s['display_path'] = _display_path(s['path'])
        s['created_str'] = time.strftime(TIME_FORMAT, time.localtime(s['created_at']))
        s['expires_str'] = time.strftime(TIME_FORMAT, time.localtime(s['expires_at']))
        prefix = {'file': '/f/', 'dir': '/d/', 'git': '/git/'}[s['type']]
        cfg = load_config()
        base_url = cfg.get('base_url', '')
        s['url'] = f'{base_url.rstrip("/")}{prefix}{s["token"]}' if base_url else f'{prefix}{s["token"]}'

    active_count = sum(1 for s in shares if s['status'] == STATUS_ACTIVE)
    bottle.response.content_type = 'text/html; charset=utf-8'
    return render_template('dashboard.html',
        shares=shares,
        share_count=len(shares),
        active_count=active_count,
    )


# --- File serving (existing) ---

@app.route('/f/<token>')
@app.route('/f/<token>/<filename>')
def serve_file(token, filename=None):
    row, status = lookup_authorization(token)

    if status == STATUS_NOT_FOUND:
        bottle.abort(404, 'Not found')

    if status == STATUS_EXPIRED:
        result = _handle_expired(row, 'filename', token, 'authorizations')
        if result is not None:
            return result

    filepath = row['filepath']
    if not os.path.isfile(filepath):
        bottle.abort(404, 'File no longer exists on disk')

    head = bottle.request.query.get('head')
    tail = bottle.request.query.get('tail')
    head = int(head) if head else None
    tail = int(tail) if tail else None

    renderer = get_renderer(filepath)
    html = renderer.render(filepath, head=head, tail=tail)
    if row['live'] and isinstance(html, str) and '</body>' in html:
        html = _inject_live_js(html, token)
    return html


# --- Live poll endpoint ---

@app.route('/live/<token>/poll')
def live_poll(token):
    """Poll for file changes. Returns JSON {changed, mtime}."""
    since = float(bottle.request.query.get('since', 0))

    # Try file authorizations first, then dir
    row, status = lookup_authorization(token)
    if status == STATUS_NOT_FOUND:
        row, status = lookup_dir_authorization(token)
    if status == STATUS_NOT_FOUND:
        bottle.abort(404, 'Not found')
    if status == STATUS_EXPIRED:
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'expired': True})

    # Get the path to check
    filepath = row['filepath'] if 'filepath' in row.keys() else row['dirpath']
    if not filepath or not os.path.exists(filepath):
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'changed': False, 'mtime': 0, 'deleted': True})

    try:
        mtime = os.stat(filepath).st_mtime
    except OSError:
        mtime = 0

    bottle.response.content_type = 'application/json'
    bottle.response.headers['Cache-Control'] = 'no-cache'
    return json_mod.dumps({'changed': mtime > since, 'mtime': mtime})


def _inject_live_js(html, token):
    """Inject live reload JavaScript before </body>."""
    script = (
        '<script>'
        '(function(){'
        'var mtime=0;'
        'function poll(){'
        'fetch("/live/' + token + '/poll?since="+mtime)'
        '.then(function(r){return r.json()})'
        '.then(function(d){'
        'if(d.expired||d.deleted){clearInterval(iv);return}'
        'if(d.changed){mtime=d.mtime;location.reload()}'
        'else if(!mtime){mtime=d.mtime}'
        '})'
        '.catch(function(){});'
        '}'
        'var iv=setInterval(poll,2000);'
        'poll();'
        '})();'
        '</script>'
    )
    return html.replace('</body>', script + '</body>')


# --- Git serving (existing) ---

@app.route('/git/<token>')
def serve_git(token):
    row, status = lookup_git_authorization(token)

    if status == STATUS_NOT_FOUND:
        bottle.abort(404, 'Not found')

    if status == STATUS_EXPIRED:
        result = _handle_expired(row, 'commit_hash', token, 'git_authorizations')
        if result is not None:
            return result

    repo_path = row['repo_path']
    commit_hash = row['commit_hash']

    try:
        info = get_git_commit_info(repo_path, commit_hash)
    except Exception as e:
        bottle.abort(500, f'Failed to read git commit: {e}')

    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import DiffLexer

    formatter = HtmlFormatter(style='github-dark', cssclass='highlight', nowrap=False)
    lexer = DiffLexer()
    pygments_css = _dual_pygments_css(nowrap=False)

    files_html = []
    for f in info['files']:
        stats = f'+{f["added"]} -{f["deleted"]}'
        diff_highlighted = highlight(f['diff'], lexer, formatter) if f['diff'] else '<pre>No diff available</pre>'
        files_html.append(
            f'<details><summary><span class="file-path">{_html_escape(f["path"])}</span>'
            f' <span class="file-stats">({stats})</span></summary>'
            f'<div class="diff-content">{diff_highlighted}</div></details>'
        )

    repo_display = _display_path(repo_path)
    short_hash = info['hash'][:12]
    body_html = f'<p class="commit-body">{_html_escape(info["body"])}</p>' if info['body'] else ''

    bottle.response.content_type = 'text/html; charset=utf-8'
    return render_template('git.html',
        repo_path=_html_escape(repo_display),
        short_hash=short_hash,
        full_hash=info['hash'],
        author_name=_html_escape(info['author_name']),
        author_email=_html_escape(info['author_email']),
        date=_html_escape(info['date']),
        subject=_html_escape(info['subject']),
        body_html=body_html,
        files_html='\n'.join(files_html),
        file_count=len(info['files']),
        pygments_css=pygments_css,
    )


# --- Directory browsing ---

def _get_dir_auth(token):
    """Validate dir token, handle expired/not_found. Returns row or aborts."""
    row, status = lookup_dir_authorization(token)
    if status == STATUS_NOT_FOUND:
        bottle.abort(404, 'Not found')
    if status == STATUS_EXPIRED:
        result = _handle_expired(row, 'dirname', token, 'dir_authorizations')
        if result is not None:
            bottle.response.content_type = 'text/html; charset=utf-8'
            return None, result
    return row, None


def _validate_dir_path(dirpath, rel_path, excludes):
    """Validate a relative path within a directory share. Returns abs_path or aborts."""
    # Reject obvious traversal attempts
    if '..' in rel_path.split('/') or rel_path.startswith('/'):
        bottle.abort(403, 'Invalid path')

    abs_path = os.path.join(dirpath, rel_path)
    if not is_safe_subpath(dirpath, abs_path):
        bottle.abort(403, 'Path traversal denied')

    if not os.path.exists(abs_path):
        bottle.abort(404, 'File not found')

    # Check excludes
    from .utils import _is_excluded
    parts = rel_path.split('/')
    for i, part in enumerate(parts):
        is_dir = i < len(parts) - 1 or os.path.isdir(abs_path)
        if _is_excluded(part, is_dir, excludes):
            bottle.abort(403, 'Access denied')

    return abs_path


def _get_excludes(row):
    """Parse the excludes JSON from a directory authorization row."""
    return json_mod.loads(row['excludes'])


def _render_dir_browser(row, initial_file=''):
    """Render the directory browser HTML for a given directory authorization row."""
    dirpath = row['dirpath']
    if not os.path.isdir(dirpath):
        bottle.abort(404, 'Directory no longer exists on disk')

    excludes = _get_excludes(row)

    try:
        tree = walk_directory(dirpath, excludes)
    except ValueError as e:
        bottle.abort(413, str(e))

    cfg = load_config()
    base_path = cfg.get('base_url', '').rstrip('/')

    bottle.response.content_type = 'text/html; charset=utf-8'
    html = render_template('dir_browser.html',
        dirname=_html_escape(row['dirname']),
        token=row['token'],
        tree_json=_js_safe_json(tree),
        expires_at=f'{row["expires_at"]:.0f}',
        initial_file=_js_string_escape(initial_file),
        base_path=_js_string_escape(base_path),
    )
    if row['live'] and '</body>' in html:
        html = _inject_live_js(html, row['token'])
    return html


@app.route('/d/<token>')
@app.route('/d/<token>/')
def serve_dir(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        return expired_resp

    return _render_dir_browser(row)


# API routes MUST be defined before the catch-all <filepath:path> route
@app.route('/d/<token>/api/tree')
def dir_api_tree(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        bottle.abort(403, 'Expired')

    dirpath = row['dirpath']
    excludes = _get_excludes(row)

    try:
        tree = walk_directory(dirpath, excludes)
    except ValueError as e:
        bottle.abort(413, str(e))

    bottle.response.content_type = 'application/json'
    return json_mod.dumps({'tree': tree, 'dirname': row['dirname'], 'token': token})


@app.route('/d/<token>/api/file')
def dir_api_file(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        bottle.abort(403, 'Expired')

    rel_path = bottle.request.query.get('path', '')
    if not rel_path:
        bottle.abort(400, 'Missing path parameter')

    dirpath = row['dirpath']
    excludes = _get_excludes(row)
    abs_path = _validate_dir_path(dirpath, rel_path, excludes)

    file_type = get_file_type(abs_path)
    cfg = load_config()
    base_url = cfg.get('base_url', '').rstrip('/')

    try:
        file_size = os.path.getsize(abs_path)
    except OSError:
        file_size = 0

    raw_url = f'{base_url}/d/{token}/raw?path={urllib.parse.quote(rel_path)}'

    if file_type in ('image', 'svg'):
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'type': 'image', 'url': raw_url})

    if file_type == 'pdf':
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'type': 'pdf', 'url': raw_url})

    if file_type in ('code', 'markdown', 'csv') and file_size <= MAX_RENDER_SIZE:
        renderer = get_renderer(abs_path)
        html_content = renderer.render(abs_path)
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'type': 'html', 'content': html_content})

    if file_type == 'media':
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'type': 'media', 'url': raw_url, 'filename': os.path.basename(abs_path), 'size': file_size})

    # Binary / unknown / oversized text
    filename = os.path.basename(abs_path)
    bottle.response.content_type = 'application/json'
    return json_mod.dumps({'type': 'binary', 'filename': filename, 'size': file_size, 'url': raw_url})


@app.route('/d/<token>/raw')
def dir_raw_file(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        bottle.abort(403, 'Expired')

    rel_path = bottle.request.query.get('path', '')
    if not rel_path:
        bottle.abort(400, 'Missing path parameter')

    dirpath = row['dirpath']
    excludes = _get_excludes(row)
    abs_path = _validate_dir_path(dirpath, rel_path, excludes)

    # Serve the file directly
    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    return bottle.static_file(filename, root=directory)


# Catch-all for deep links into directory (MUST be after API routes)
@app.route('/d/<token>/<filepath:path>')
def serve_dir_file(token, filepath):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        return expired_resp

    return _render_dir_browser(row, initial_file=filepath)
