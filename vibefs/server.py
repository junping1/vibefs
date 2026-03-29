import json as json_mod
import mimetypes
import os
import time
import urllib.parse
from collections import defaultdict
import threading

import bottle

from .config import load_config, get_owner_key
from .constants import DEFAULT_TTL, DIR_DEFAULT_TTL
from .db import (
    get_db, lookup_authorization, lookup_dir_authorization,
    lookup_git_authorization, get_git_commit_info, list_all_authorizations,
)
from .renderers import get_renderer
from .templates import (
    GIT_HTML_TEMPLATE, EXPIRED_TEMPLATE, EXPIRED_VERIFY_TEMPLATE,
    DIR_BROWSER_TEMPLATE, DASHBOARD_TEMPLATE,
    _dual_pygments_css,
)
from .utils import (
    _display_path, _html_escape, is_safe_subpath,
    walk_directory, get_file_type,
)

app = bottle.Bottle()


# --- Rate limiting ---

_rate_limits = defaultdict(list)
_rate_lock = threading.Lock()
RATE_LIMIT = 60
RATE_WINDOW = 60


@app.hook('before_request')
def rate_limit():
    ip = bottle.request.environ.get('HTTP_X_FORWARDED_FOR', bottle.request.remote_addr)
    if ip:
        ip = ip.split(',')[0].strip()
    now = time.time()
    with _rate_lock:
        _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < RATE_WINDOW]
        if len(_rate_limits[ip]) >= RATE_LIMIT:
            bottle.abort(429, 'Rate limit exceeded')
        _rate_limits[ip].append(now)


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


def _handle_expired(row, name_field, token, table='authorizations'):
    """Handle expired authorization. Returns response HTML or None if owner-authed."""
    cfg = load_config()

    # Owner cookie bypasses expiry
    if _check_owner_auth():
        ttl = cfg.get('file_ttl', DEFAULT_TTL)
        if table == 'dir_authorizations':
            ttl = cfg.get('dir_default_ttl', DIR_DEFAULT_TTL)
        db = get_db()
        db.execute(f'UPDATE {table} SET expires_at = ? WHERE token = ?', (time.time() + ttl, token))
        db.commit()
        db.close()
        return None  # Proceed to serve

    # Regular auth cookie (for backward compat with password config)
    password = cfg.get('password')
    if password and _check_expired_auth(password):
        ttl = cfg.get('file_ttl', DEFAULT_TTL)
        if table == 'dir_authorizations':
            ttl = cfg.get('dir_default_ttl', DIR_DEFAULT_TTL)
        db = get_db()
        db.execute(f'UPDATE {table} SET expires_at = ? WHERE token = ?', (time.time() + ttl, token))
        db.commit()
        db.close()
        return None  # Proceed to serve

    verify_url = f'/verify?next={bottle.request.path}' if password else ''
    return bottle.template(EXPIRED_TEMPLATE, filename=row[name_field], verify_url=verify_url)


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
    return bottle.template(EXPIRED_VERIFY_TEMPLATE, next=next_url, error='')


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
    if submitted == password:
        bottle.response.set_cookie('vibefs_auth', 'verified', secret=password, path='/', max_age=86400)
        bottle.redirect(next_url)
    else:
        return bottle.template(EXPIRED_VERIFY_TEMPLATE, next=next_url, error='Incorrect password')


# --- Owner auth (key-based) ---

@app.route('/owner/auth')
def owner_auth():
    """Authenticate owner via ?key= param, set long-lived cookie."""
    key = bottle.request.query.get('key', '')
    next_url = bottle.request.query.get('next', '/dashboard')
    if not next_url.startswith('/'):
        next_url = '/dashboard'

    owner_key = get_owner_key()
    if not key or key != owner_key:
        bottle.abort(403, 'Invalid key')

    bottle.response.set_cookie('vibefs_owner', 'owner', secret=owner_key, path='/', max_age=30 * 86400)
    bottle.redirect(next_url)


# --- Dashboard ---

@app.route('/dashboard')
def dashboard():
    # Allow ?key= param to authenticate inline
    key = bottle.request.query.get('key', '')
    if key:
        owner_key = get_owner_key()
        if key == owner_key:
            bottle.response.set_cookie('vibefs_owner', 'owner', secret=owner_key, path='/', max_age=30 * 86400)
        else:
            bottle.abort(403, 'Invalid key')
    elif not _check_owner_auth():
        bottle.abort(403, 'Access denied')

    shares = list_all_authorizations()
    for s in shares:
        s['display_path'] = _display_path(s['path'])
        s['created_str'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(s['created_at']))
        s['expires_str'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(s['expires_at']))
        prefix = {'file': '/f/', 'dir': '/d/', 'git': '/git/'}[s['type']]
        cfg = load_config()
        base_url = cfg.get('base_url', '')
        s['url'] = f'{base_url.rstrip("/")}{prefix}{s["token"]}' if base_url else f'{prefix}{s["token"]}'

    active_count = sum(1 for s in shares if s['status'] == 'active')
    bottle.response.content_type = 'text/html; charset=utf-8'
    return bottle.template(DASHBOARD_TEMPLATE.format(
        share_count=len(shares),
        active_count=active_count,
    ), shares=shares)


# --- File serving (existing) ---

@app.route('/f/<token>')
@app.route('/f/<token>/<filename>')
def serve_file(token, filename=None):
    row, status = lookup_authorization(token)

    if status == 'not_found':
        bottle.abort(404, 'Not found')

    if status == 'expired':
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
    return renderer.render(filepath, head=head, tail=tail)


# --- Git serving (existing) ---

@app.route('/git/<token>')
def serve_git(token):
    row, status = lookup_git_authorization(token)

    if status == 'not_found':
        bottle.abort(404, 'Not found')

    if status == 'expired':
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
    return GIT_HTML_TEMPLATE.format(
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
    if status == 'not_found':
        bottle.abort(404, 'Not found')
    if status == 'expired':
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


@app.route('/d/<token>')
@app.route('/d/<token>/')
def serve_dir(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        return expired_resp

    dirpath = row['dirpath']
    if not os.path.isdir(dirpath):
        bottle.abort(404, 'Directory no longer exists on disk')

    excludes = json_mod.loads(row['excludes'])

    try:
        tree = walk_directory(dirpath, excludes)
    except ValueError as e:
        bottle.abort(413, str(e))

    cfg = load_config()
    base_path = cfg.get('base_url', '').rstrip('/')

    bottle.response.content_type = 'text/html; charset=utf-8'
    return DIR_BROWSER_TEMPLATE.format(
        dirname=_html_escape(row['dirname']),
        token=token,
        tree_json=json_mod.dumps(tree),
        expires_at=f'{row["expires_at"]:.0f}',
        initial_file='',
        base_path=base_path,
    )


@app.route('/d/<token>/<filepath:path>')
def serve_dir_file(token, filepath):
    # If it's an API path, skip (handled by specific routes below)
    if filepath.startswith('api/'):
        bottle.abort(404, 'Not found')

    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        return expired_resp

    dirpath = row['dirpath']
    if not os.path.isdir(dirpath):
        bottle.abort(404, 'Directory no longer exists on disk')

    excludes = json_mod.loads(row['excludes'])

    try:
        tree = walk_directory(dirpath, excludes)
    except ValueError as e:
        bottle.abort(413, str(e))

    cfg = load_config()
    base_path = cfg.get('base_url', '').rstrip('/')

    bottle.response.content_type = 'text/html; charset=utf-8'
    return DIR_BROWSER_TEMPLATE.format(
        dirname=_html_escape(row['dirname']),
        token=token,
        tree_json=json_mod.dumps(tree),
        expires_at=f'{row["expires_at"]:.0f}',
        initial_file=_html_escape(filepath),
        base_path=base_path,
    )


@app.route('/d/<token>/api/tree')
def dir_api_tree(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        bottle.abort(403, 'Expired')

    dirpath = row['dirpath']
    excludes = json_mod.loads(row['excludes'])

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
    excludes = json_mod.loads(row['excludes'])
    abs_path = _validate_dir_path(dirpath, rel_path, excludes)

    file_type = get_file_type(abs_path)
    cfg = load_config()
    base_url = cfg.get('base_url', '').rstrip('/')

    if file_type == 'image':
        raw_url = f'{base_url}/d/{token}/raw?path={urllib.parse.quote(rel_path)}'
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'type': 'image', 'url': raw_url})

    if file_type in ('code', 'markdown'):
        renderer = get_renderer(abs_path)
        html_content = renderer.render(abs_path)
        bottle.response.content_type = 'application/json'
        return json_mod.dumps({'type': 'html', 'content': html_content})

    # Binary / unknown
    raw_url = f'{base_url}/d/{token}/raw?path={urllib.parse.quote(rel_path)}'
    filename = os.path.basename(abs_path)
    try:
        size = os.path.getsize(abs_path)
    except OSError:
        size = 0
    bottle.response.content_type = 'application/json'
    return json_mod.dumps({'type': 'binary', 'filename': filename, 'size': size, 'url': raw_url})


@app.route('/d/<token>/raw')
def dir_raw_file(token):
    row, expired_resp = _get_dir_auth(token)
    if expired_resp is not None:
        bottle.abort(403, 'Expired')

    rel_path = bottle.request.query.get('path', '')
    if not rel_path:
        bottle.abort(400, 'Missing path parameter')

    dirpath = row['dirpath']
    excludes = json_mod.loads(row['excludes'])
    abs_path = _validate_dir_path(dirpath, rel_path, excludes)

    # Serve the file directly
    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    return bottle.static_file(filename, root=directory)
