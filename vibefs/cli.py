import atexit
import os
import sys
import time

import click

from .constants import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_TTL, ensure_state_dir
from .config import load_config, save_config
from .db import (
    add_authorization, remove_authorization, list_authorizations,
    add_git_authorization, get_db,
)
from .daemon import (
    read_pid, write_pid, remove_pid,
    is_daemon_running, start_daemon, stop_daemon, start_cleanup_timer,
)
from .server import app
from .utils import _display_path

VALID_CONFIG_KEYS = ['base_url', 'file_ttl', 'auto_stop', 'password', 'pygments.style', 'pygments.linenos']


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
    elif key == 'file_ttl':
        value = int(value)
    target[parts[-1]] = value


@click.group()
def cli():
    """vibefs — Vibe File Server

    A simple, secure file preview service for sharing files via time-limited URLs.
    """
    pass


@cli.command()
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port to listen on')
@click.option('--host', default=DEFAULT_HOST, show_default=True, help='Host to bind to')
@click.option('--foreground', is_flag=True, default=False, help='Run in foreground (no PID file cleanup timer)')
def serve(port, host, foreground):
    """Start the web server."""
    ensure_state_dir()
    write_pid()
    atexit.register(remove_pid)

    if not foreground:
        cfg = load_config()
        if cfg.get('auto_stop', False):
            start_cleanup_timer()

    click.echo(f'vibefs serving on http://{host}:{port} (pid {os.getpid()})')
    app.run(host=host, port=port, quiet=True)


@cli.command()
@click.argument('path')
@click.option('--ttl', default=None, type=int, help=f'Time-to-live in seconds (default: config file_ttl or {DEFAULT_TTL})')
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port for URL generation')
@click.option('--host', default='localhost', show_default=True, help='Host for URL generation')
@click.option('--head', default=None, type=int, help='Only show first N lines')
@click.option('--tail', default=None, type=int, help='Only show last N lines')
def allow(path, ttl, port, host, head, tail):
    """Authorize a file for access, auto-start daemon if needed, and print its URL."""
    ensure_state_dir()
    if ttl is None:
        cfg = load_config()
        ttl = cfg.get('file_ttl', DEFAULT_TTL)
    token, filename, is_new = add_authorization(path, ttl)
    base_url = load_config().get('base_url')
    if base_url:
        url = f'{base_url.rstrip("/")}/f/{token}/{filename}'
    else:
        url = f'http://{host}:{port}/f/{token}/{filename}'
    params = []
    if head is not None:
        params.append(f'head={head}')
    if tail is not None:
        params.append(f'tail={tail}')
    if params:
        url += '?' + '&'.join(params)
    click.echo(url)
    if not is_new:
        click.echo('(existing authorization extended)', err=True)

    if not is_daemon_running():
        start_daemon(port, DEFAULT_HOST)


@cli.command('allow-git')
@click.argument('repo_path')
@click.argument('commit_hash')
@click.option('--ttl', default=None, type=int, help=f'Time-to-live in seconds (default: config file_ttl or {DEFAULT_TTL})')
@click.option('--port', default=DEFAULT_PORT, show_default=True, help='Port for URL generation')
def allow_git(repo_path, commit_hash, ttl, port):
    """Authorize a git commit for viewing and print its URL."""
    ensure_state_dir()
    if ttl is None:
        cfg = load_config()
        ttl = cfg.get('file_ttl', DEFAULT_TTL)
    try:
        token, is_new = add_git_authorization(repo_path, commit_hash, ttl)
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    base_url = load_config().get('base_url')
    if base_url:
        url = f'{base_url.rstrip("/")}/git/{token}'
    else:
        url = f'http://localhost:{port}/git/{token}'
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
def list_cmd():
    """List currently authorized files and git commits."""
    rows = list_authorizations()
    now = time.time()
    has_any = False

    if rows:
        has_any = True
        click.echo('Files:')
        for row in rows:
            remaining = row['expires_at'] - now
            status = f'{int(remaining)}s remaining' if remaining > 0 else 'expired'
            click.echo(f'  {row["token"]}  {row["filepath"]}  [{status}]')

    db = get_db()
    git_rows = db.execute(
        'SELECT token, repo_path, commit_hash, created_at, expires_at FROM git_authorizations ORDER BY created_at DESC'
    ).fetchall()
    db.close()

    if git_rows:
        has_any = True
        click.echo('Git commits:')
        for row in git_rows:
            remaining = row['expires_at'] - now
            status = f'{int(remaining)}s remaining' if remaining > 0 else 'expired'
            short_hash = row['commit_hash'][:12]
            click.echo(f'  {row["token"]}  {_display_path(row["repo_path"])} {short_hash}  [{status}]')

    if not has_any:
        click.echo('No active authorizations.')


@cli.command()
def stop():
    """Stop the running daemon."""
    if stop_daemon():
        click.echo('Daemon stopped.')
    else:
        click.echo('Daemon is not running.', err=True)


@cli.command()
def status():
    """Check if the daemon is running."""
    pid = read_pid()
    if is_daemon_running():
        click.echo(f'Daemon is running (pid {pid}).')
    else:
        click.echo('Daemon is not running.')


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
