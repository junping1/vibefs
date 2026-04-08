"""Cloudflare Quick Tunnel management for vibefs."""

import re
import shutil
import subprocess
import threading


def start_tunnel(port, timeout=30):
    """Start a cloudflared Quick Tunnel and return (process, tunnel_url).

    Raises RuntimeError if cloudflared is not installed.
    Raises TimeoutError if the tunnel URL is not found within `timeout` seconds.
    """
    if not shutil.which('cloudflared'):
        raise RuntimeError(
            'cloudflared is not installed.\n'
            'Install it:\n'
            '  macOS:  brew install cloudflared\n'
            '  Linux:  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared && chmod +x cloudflared\n'
            '  Or see: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/'
        )

    proc = subprocess.Popen(
        ['cloudflared', 'tunnel', '--url', f'http://localhost:{port}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    url_pattern = re.compile(r'(https://[a-z0-9-]+\.trycloudflare\.com)')
    found_url = [None]
    event = threading.Event()

    def read_stderr():
        for line in proc.stderr:
            match = url_pattern.search(line)
            if match and not found_url[0]:
                found_url[0] = match.group(1)
                event.set()
        # stderr closed = process exited

    reader = threading.Thread(target=read_stderr, daemon=True)
    reader.start()

    if not event.wait(timeout=timeout):
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError(f'Timed out waiting for tunnel URL ({timeout}s). Check cloudflared logs.')

    return proc, found_url[0]


def stop_tunnel(proc):
    """Stop the cloudflared tunnel process."""
    if proc.poll() is not None:
        return  # already exited
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)
