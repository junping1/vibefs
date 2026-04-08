import atexit
import json
import os
import re
import secrets
import sys
import time

import click

from .constants import (
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_TTL, DIR_DEFAULT_TTL, DEFAULT_EXCLUDES,
    SHARES_DIR, SHARE_TYPE_MAP, MAX_SHARE_SIZE, TUNNEL_URL_PATH, ensure_state_dir,
    STATUS_ACTIVE, STATUS_EXPIRED,
)
from .config import load_config, save_config, get_owner_key
from .db import (
    add_authorization, remove_authorization, list_authorizations,
    add_git_authorization, add_dir_authorization, list_dir_authorizations,
    cleanup_expired_shares, get_db,
)
from .daemon import (
    read_pid, write_pid, remove_pid,
    is_daemon_running, start_daemon, stop_daemon, start_cleanup_timer,
)
from .server import app
from .utils import _display_path

VALID_CONFIG_KEYS = ['base_url', 'port', 'file_ttl', 'dir_default_ttl', 'auto_stop', 'password', 'default_excludes', 'pygments.style', 'pygments.linenos']


def _get_nested(cfg, key):
    parts = key.split('.')
    value = cfg
    for part in parts:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
        if value is None:
            return None
    return value


def _set_nested(cfg, key, value):
    parts = key.split('.')
    target = cfg
    for part in parts[:-1]:
        if part not in target or not isinstance(target[part], dict):
            target[part] = {}
        target = target[part]
    if key == 'pygments.linenos':
        value = value.lower() in ('true', '1', 'yes', 'table', 'inline')
    elif key == 'auto_stop':
        value = value.lower() in ('true', '1', 'yes')
    elif key in ('file_ttl', 'port'):
        value = int(value)
    target[parts[-1]] = value


def _build_url(cfg, prefix, token, port, host='localhost'):
    """Build a share URL using tunnel URL, config base_url, or host:port fallback."""
    # Tunnel URL takes highest priority
    if os.path.isfile(TUNNEL_URL_PATH):
        with open(TUNNEL_URL_PATH) as f:
            tunnel_url = f.read().strip()
        if tunnel_url:
            return f'{tunnel_url.rstrip("/")}/{prefix}/{token}'
    base_url = cfg.get('base_url')
    if base_url:
        return f'{base_url.rstrip("/")}/{prefix}/{token}'
    return f'http://{host}:{port}/{prefix}/{token}'


@click.group()
def cli():
    """vibefs — Vibe File Server

    Share files, directories, and content via time-limited preview URLs.
    Renders code with syntax highlighting, markdown as formatted HTML, and images inline.

    \b
    Quick start:
      vibefs allow ~/file.md              Share a file
      vibefs allow ~/project/             Share a directory (browsable UI)
      git diff | vibefs share --type diff Pipe content to share
      vibefs list --json                  List all shares as JSON
      vibefs serve --tunnel               Start server with public URL
    """
    pass


@cli.command()
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port to listen on')
@click.option('--host', default=DEFAULT_HOST, show_default=True, help='Host to bind to')
@click.option('--foreground', is_flag=True, default=False, help='Run in foreground (no auto-stop timer)')
@click.option('--tunnel', is_flag=True, default=False, help='Start a cloudflared Quick Tunnel for public access (no account needed)')
def serve(port, host, foreground, tunnel):
    """Start the web server.

    By default, serves on localhost. Use --tunnel to get a public URL via
    Cloudflare Quick Tunnel (requires cloudflared binary installed).
    """
    ensure_state_dir()
    write_pid()
    atexit.register(remove_pid)

    tunnel_proc = None
    if tunnel:
        from .tunnel import start_tunnel, stop_tunnel
        try:
            tunnel_proc, tunnel_url = start_tunnel(port)
            click.echo(f'Tunnel active: {tunnel_url}', err=True)
            # Write tunnel URL for other CLI commands to use
            with open(TUNNEL_URL_PATH, 'w') as f:
                f.write(tunnel_url)
            atexit.register(lambda: os.path.isfile(TUNNEL_URL_PATH) and os.remove(TUNNEL_URL_PATH))
            atexit.register(stop_tunnel, tunnel_proc)
        except RuntimeError as e:
            click.echo(f'Tunnel error: {e}', err=True)
            sys.exit(1)

    if not foreground:
        cfg = load_config()
        if cfg.get('auto_stop', False):
            start_cleanup_timer()

    click.echo(f'vibefs serving on http://{host}:{port} (pid {os.getpid()})')
    from waitress import serve as waitress_serve
    waitress_serve(app, host=host, port=port, _quiet=True)


@cli.command()
@click.argument('path')
@click.option('--ttl', default=None, type=int, help=f'Time-to-live in seconds (default: {DEFAULT_TTL} for files, {DIR_DEFAULT_TTL} for dirs)')
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port for URL generation')
@click.option('--host', default='localhost', show_default=True, help='Host for URL generation')
@click.option('--head', default=None, type=int, help='Only show first N lines (files only)')
@click.option('--tail', default=None, type=int, help='Only show last N lines (files only)')
@click.option('--exclude', multiple=True, help='Additional exclude patterns for directory shares')
@click.option('--live', is_flag=True, default=False, help='Enable live preview (auto-refresh on file changes)')
@click.option('--json', 'output_json', is_flag=True, default=False, help='Output result as JSON')
def allow(path, ttl, port, host, head, tail, exclude, live, output_json):
    """Share a file or directory via a time-limited preview URL.

    \b
    Examples:
      vibefs allow ~/notes/todo.md           Share a markdown file
      vibefs allow ~/project/ --ttl 7200     Share a directory for 2 hours
      vibefs allow ~/data/ --exclude '*.log' Exclude log files
      vibefs allow ~/doc.md --live           Auto-refresh on changes
      vibefs allow ~/file.py --json          Output URL as JSON
    """
    ensure_state_dir()
    abs_path = os.path.abspath(path)
    cfg = load_config()
    port = cfg.get('port', port)
    share_type = None
    expires_at = None

    if os.path.isdir(abs_path):
        share_type = 'dir'
        if head is not None or tail is not None:
            click.echo('Warning: --head and --tail are ignored for directory shares', err=True)
        if ttl is None:
            ttl = cfg.get('dir_default_ttl', DIR_DEFAULT_TTL)
        excludes = list(cfg.get('default_excludes', DEFAULT_EXCLUDES)) + list(exclude)
        token, dirname, is_new = add_dir_authorization(abs_path, ttl, excludes, live=live)
        url = _build_url(cfg, 'd', token, port, host)
        expires_at = time.time() + ttl
    elif os.path.isfile(abs_path):
        share_type = 'file'
        if ttl is None:
            ttl = cfg.get('file_ttl', DEFAULT_TTL)
        token, filename, is_new = add_authorization(path, ttl, live=live)
        url = _build_url(cfg, 'f', token, port, host)
        expires_at = time.time() + ttl
        params = []
        if head is not None:
            params.append(f'head={head}')
        if tail is not None:
            params.append(f'tail={tail}')
        if params:
            url += '?' + '&'.join(params)
    else:
        if output_json:
            click.echo(json.dumps({'error': f'Path not found: {abs_path}'}))
        else:
            click.echo(f'Path not found: {abs_path}', err=True)
        sys.exit(1)

    if output_json:
        click.echo(json.dumps({
            'url': url,
            'token': token,
            'type': share_type,
            'path': abs_path,
            'ttl': ttl,
            'expires_at': expires_at,
            'live': live,
            'is_new': is_new,
        }))
    else:
        click.echo(url)
        if not is_new:
            click.echo('(existing authorization extended)', err=True)
        if live:
            click.echo('(live preview enabled)', err=True)

    if not is_daemon_running():
        start_daemon(port, DEFAULT_HOST)


@cli.command()
@click.option('--type', 'share_type', type=click.Choice(list(SHARE_TYPE_MAP.keys())), default='text', help='Content type for rendering')
@click.option('--content', default=None, help='Inline content string to share')
@click.option('--title', default=None, help='Title for the shared content (used in filename)')
@click.option('--ttl', default=None, type=int, help=f'Time-to-live in seconds (default: config file_ttl or {DEFAULT_TTL})')
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port for URL generation')
@click.option('--host', default='localhost', show_default=True, help='Host for URL generation')
@click.option('--json', 'output_json', is_flag=True, default=False, help='Output result as JSON')
def share(share_type, content, title, ttl, port, host, output_json):
    """Share content from stdin or inline text as a temporary file.

    \b
    Examples:
      echo "# Hello" | vibefs share --type markdown
      git diff | vibefs share --type diff --title "my changes"
      vibefs share --content "print('hi')" --type python
      cat data.csv | vibefs share --type text --ttl 7200
    """
    ensure_state_dir()

    # Read content
    if content is not None:
        text = content
    elif not sys.stdin.isatty():
        text = sys.stdin.read(MAX_SHARE_SIZE + 1)
        if len(text) > MAX_SHARE_SIZE:
            click.echo(f'Error: input exceeds {MAX_SHARE_SIZE // (1024*1024)}MB limit', err=True)
            sys.exit(1)
    else:
        click.echo('Error: provide --content or pipe data via stdin', err=True)
        click.echo('  echo "content" | vibefs share --type markdown', err=True)
        sys.exit(1)

    # Create temp file
    os.makedirs(SHARES_DIR, exist_ok=True)
    ext = SHARE_TYPE_MAP.get(share_type, '.txt')
    slug = re.sub(r'[^a-zA-Z0-9_-]', '-', title)[:40] if title else 'share'
    filename = f'{slug}_{secrets.token_hex(4)}{ext}'
    filepath = os.path.join(SHARES_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(text)

    # Share it
    cfg = load_config()
    port = cfg.get('port', port)
    if ttl is None:
        ttl = cfg.get('file_ttl', DEFAULT_TTL)
    token, _, is_new = add_authorization(filepath, ttl)
    url = _build_url(cfg, 'f', token, port, host)

    if output_json:
        click.echo(json.dumps({
            'url': url,
            'token': token,
            'type': share_type,
            'path': filepath,
            'ttl': ttl,
            'expires_at': time.time() + ttl,
        }))
    else:
        click.echo(url)

    if not is_daemon_running():
        start_daemon(port, DEFAULT_HOST)


@cli.command('allow-git')
@click.argument('repo_path')
@click.argument('commit_hash')
@click.option('--ttl', default=None, type=int, help=f'Time-to-live in seconds (default: config file_ttl or {DEFAULT_TTL})')
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port for URL generation')
@click.option('--json', 'output_json', is_flag=True, default=False, help='Output result as JSON')
def allow_git(repo_path, commit_hash, ttl, port, output_json):
    """Share a git commit with syntax-highlighted diffs."""
    ensure_state_dir()
    cfg = load_config()
    port = cfg.get('port', port)
    if ttl is None:
        ttl = cfg.get('file_ttl', DEFAULT_TTL)
    try:
        token, is_new = add_git_authorization(repo_path, commit_hash, ttl)
    except ValueError as e:
        if output_json:
            click.echo(json.dumps({'error': str(e)}))
        else:
            click.echo(str(e), err=True)
        sys.exit(1)
    url = _build_url(cfg, 'git', token, port)

    if output_json:
        click.echo(json.dumps({
            'url': url,
            'token': token,
            'type': 'git',
            'repo_path': os.path.abspath(repo_path),
            'commit_hash': commit_hash,
            'ttl': ttl,
            'expires_at': time.time() + ttl,
        }))
    else:
        click.echo(url)
        if not is_new:
            click.echo('(existing authorization extended)', err=True)

    if not is_daemon_running():
        start_daemon(port, DEFAULT_HOST)


@cli.command()
@click.argument('token')
def revoke(token):
    """Revoke access to a file by its token."""
    if remove_authorization(token):
        click.echo(f'Revoked: {token}')
    else:
        click.echo(f'Token not found: {token}', err=True)


@cli.command('list')
@click.option('--json', 'output_json', is_flag=True, default=False, help='Output list as JSON array')
def list_cmd(output_json):
    """List all shared files, directories, and git commits."""
    now = time.time()
    cfg = load_config()
    all_shares = []

    for row in list_authorizations():
        remaining = row['expires_at'] - now
        entry = {
            'token': row['token'],
            'type': 'file',
            'path': row['filepath'],
            'status': STATUS_ACTIVE if remaining > 0 else STATUS_EXPIRED,
            'remaining': max(0, int(remaining)),
            'expires_at': row['expires_at'],
            'url': _build_url(cfg, 'f', row['token'], DEFAULT_PORT),
        }
        all_shares.append(entry)

    db = get_db()
    for row in db.execute('SELECT token, repo_path, commit_hash, created_at, expires_at FROM git_authorizations ORDER BY created_at DESC').fetchall():
        remaining = row['expires_at'] - now
        all_shares.append({
            'token': row['token'],
            'type': 'git',
            'path': row['repo_path'],
            'name': row['commit_hash'][:12],
            'status': STATUS_ACTIVE if remaining > 0 else STATUS_EXPIRED,
            'remaining': max(0, int(remaining)),
            'expires_at': row['expires_at'],
            'url': _build_url(cfg, 'git', row['token'], DEFAULT_PORT),
        })
    db.close()

    for row in list_dir_authorizations():
        remaining = row['expires_at'] - now
        all_shares.append({
            'token': row['token'],
            'type': 'dir',
            'path': row['dirpath'],
            'status': STATUS_ACTIVE if remaining > 0 else STATUS_EXPIRED,
            'remaining': max(0, int(remaining)),
            'expires_at': row['expires_at'],
            'url': _build_url(cfg, 'd', row['token'], DEFAULT_PORT),
        })

    if output_json:
        click.echo(json.dumps(all_shares, indent=2))
        return

    if not all_shares:
        click.echo('No active authorizations.')
        return

    files = [s for s in all_shares if s['type'] == 'file']
    dirs = [s for s in all_shares if s['type'] == 'dir']
    gits = [s for s in all_shares if s['type'] == 'git']

    if files:
        click.echo('Files:')
        for s in files:
            status = f'{s["remaining"]}s remaining' if s['status'] == STATUS_ACTIVE else STATUS_EXPIRED
            click.echo(f'  {s["token"]}  {s["path"]}  [{status}]')
    if gits:
        click.echo('Git commits:')
        for s in gits:
            status = f'{s["remaining"]}s remaining' if s['status'] == STATUS_ACTIVE else STATUS_EXPIRED
            click.echo(f'  {s["token"]}  {_display_path(s["path"])} {s["name"]}  [{status}]')
    if dirs:
        click.echo('Directories:')
        for s in dirs:
            status = f'{s["remaining"]}s remaining' if s['status'] == STATUS_ACTIVE else STATUS_EXPIRED
            click.echo(f'  {s["token"]}  {_display_path(s["path"])}  [{status}]')


@cli.command()
@click.option('--json', 'output_json', is_flag=True, default=False, help='Output status as JSON')
def status(output_json):
    """Check if the daemon is running."""
    pid = read_pid()
    running = is_daemon_running()
    if output_json:
        click.echo(json.dumps({'running': running, 'pid': pid}))
    elif running:
        click.echo(f'Daemon is running (pid {pid}).')
    else:
        click.echo('Daemon is not running.')


@cli.command()
def stop():
    """Stop the running daemon."""
    if stop_daemon():
        click.echo('Daemon stopped.')
    else:
        click.echo('Daemon is not running.', err=True)


@cli.command('owner-url')
def owner_url():
    """Print the owner dashboard URL (auto-generates key on first run)."""
    key = get_owner_key()
    cfg = load_config()
    base_url = cfg.get('base_url', '')
    if base_url:
        url = f'{base_url.rstrip("/")}/dashboard?key={key}'
    else:
        url = f'http://localhost:{DEFAULT_PORT}/dashboard?key={key}'
    click.echo(url)
    click.echo('Open this URL once in your browser — it sets a 30-day cookie.', err=True)
    click.echo('After that, /dashboard works without the key.', err=True)


@cli.group()
def config():
    """Get or set configuration values."""
    pass


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a config value (e.g. vibefs config set pygments.style dracula)."""
    if key not in VALID_CONFIG_KEYS:
        click.echo(f'Unknown config key: {key}. Valid keys: {", ".join(VALID_CONFIG_KEYS)}', err=True)
        sys.exit(1)
    cfg = load_config()
    _set_nested(cfg, key, value)
    save_config(cfg)
    click.echo(f'{key} = {_get_nested(cfg, key)}')


@config.command('get')
@click.argument('key')
def config_get(key):
    """Get a config value (e.g. vibefs config get pygments.style)."""
    if key not in VALID_CONFIG_KEYS:
        click.echo(f'Unknown config key: {key}. Valid keys: {", ".join(VALID_CONFIG_KEYS)}', err=True)
        sys.exit(1)
    cfg = load_config()
    value = _get_nested(cfg, key)
    if value is None:
        click.echo(f'{key}: (not set)')
    else:
        click.echo(f'{key} = {value}')
