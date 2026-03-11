import os
import time

import bottle

from .config import load_config
from .constants import DEFAULT_TTL
from .db import get_db, lookup_authorization, lookup_git_authorization, get_git_commit_info
from .renderers import get_renderer
from .templates import GIT_HTML_TEMPLATE, EXPIRED_TEMPLATE, EXPIRED_VERIFY_TEMPLATE, _dual_pygments_css
from .utils import _display_path, _html_escape

app = bottle.Bottle()


def _check_expired_auth(password):
    """Check if user has a valid auth cookie. Returns True if verified."""
    return bottle.request.get_cookie('vibefs_auth', secret=password) == 'verified'


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


@app.route('/f/<token>')
@app.route('/f/<token>/<filename>')
def serve_file(token, filename=None):
    row, status = lookup_authorization(token)

    if status == 'not_found':
        bottle.abort(404, 'Not found')

    if status == 'expired':
        cfg = load_config()
        password = cfg.get('password')
        if password and _check_expired_auth(password):
            ttl = cfg.get('file_ttl', DEFAULT_TTL)
            db = get_db()
            db.execute('UPDATE authorizations SET expires_at = ? WHERE token = ?', (time.time() + ttl, token))
            db.commit()
            db.close()
        else:
            verify_url = f'/verify?next={bottle.request.path}' if password else ''
            return bottle.template(EXPIRED_TEMPLATE, filename=row['filename'], verify_url=verify_url)

    filepath = row['filepath']
    if not os.path.isfile(filepath):
        bottle.abort(404, 'File no longer exists on disk')

    head = bottle.request.query.get('head')
    tail = bottle.request.query.get('tail')
    head = int(head) if head else None
    tail = int(tail) if tail else None

    renderer = get_renderer(filepath)
    return renderer.render(filepath, head=head, tail=tail)


@app.route('/git/<token>')
def serve_git(token):
    row, status = lookup_git_authorization(token)

    if status == 'not_found':
        bottle.abort(404, 'Not found')

    if status == 'expired':
        cfg = load_config()
        password = cfg.get('password')
        if password and _check_expired_auth(password):
            ttl = cfg.get('file_ttl', DEFAULT_TTL)
            db = get_db()
            db.execute('UPDATE git_authorizations SET expires_at = ? WHERE token = ?', (time.time() + ttl, token))
            db.commit()
            db.close()
        else:
            verify_url = f'/verify?next={bottle.request.path}' if password else ''
            return bottle.template(EXPIRED_TEMPLATE, filename='git commit', verify_url=verify_url)

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
