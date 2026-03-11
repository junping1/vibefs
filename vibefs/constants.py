import os

DEFAULT_PORT = 17173
DEFAULT_HOST = '0.0.0.0'
DEFAULT_TTL = 3600  # 1 hour
TOKEN_LENGTH = 2  # bytes, produces 4 hex chars
CLEANUP_INTERVAL = 60  # seconds between auto-stop checks

STATE_DIR = os.path.expanduser('~/.vibefs')
DB_PATH = os.path.join(STATE_DIR, 'vibefs.db')
PID_PATH = os.path.join(STATE_DIR, 'vibefs.pid')
LOG_PATH = os.path.join(STATE_DIR, 'vibefs.log')
CONFIG_PATH = os.path.join(STATE_DIR, 'config.json')


def ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)
