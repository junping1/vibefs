import os
import signal
import subprocess
import sys
import threading
import time

import click

from .constants import CLEANUP_INTERVAL, DEFAULT_HOST, LOG_PATH, PID_PATH, ensure_state_dir
from .config import load_config
from .db import has_active_authorizations, cleanup_expired_shares


def read_pid():
    """Read PID from file. Returns int or None."""
    if not os.path.exists(PID_PATH):
        return None
    with open(PID_PATH) as f:
        content = f.read().strip()
    if not content:
        return None
    return int(content)


def write_pid():
    """Write current process PID to file."""
    ensure_state_dir()
    with open(PID_PATH, 'w') as f:
        f.write(str(os.getpid()))


def remove_pid():
    """Remove PID file if it exists."""
    if os.path.exists(PID_PATH):
        os.remove(PID_PATH)


def is_daemon_running():
    """Check if daemon is alive via PID file. Cleans stale PID files."""
    pid = read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        remove_pid()
        return False
    except PermissionError:
        return True


def start_daemon(port, host):
    """Fork a background daemon process running 'vibefs serve'."""
    ensure_state_dir()
    log_file = open(LOG_PATH, 'a')
    proc = subprocess.Popen(
        [sys.executable, '-m', 'vibefs', 'serve', '--port', str(port), '--host', host],
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,
    )
    log_file.close()
    time.sleep(0.3)
    if proc.poll() is not None:
        click.echo('Warning: daemon process exited immediately, check ~/.vibefs/vibefs.log', err=True)
    else:
        click.echo(f'Daemon started (pid {proc.pid})', err=True)


def stop_daemon():
    """Send SIGTERM to the daemon. Returns True if signal was sent."""
    pid = read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        remove_pid()
        return False


def start_cleanup_timer():
    """Start a background thread that exits the server when all authorizations expire."""

    def check_loop():
        while True:
            time.sleep(CLEANUP_INTERVAL)
            cleanup_expired_shares()
            if not has_active_authorizations():
                click.echo('All authorizations expired, shutting down.', err=True)
                remove_pid()
                os._exit(0)

    t = threading.Thread(target=check_loop, daemon=True)
    t.start()
