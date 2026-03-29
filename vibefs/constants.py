import os

DEFAULT_PORT = 17173
DEFAULT_HOST = '0.0.0.0'
DEFAULT_TTL = 3600  # 1 hour
TOKEN_LENGTH = 2  # bytes, produces 4 hex chars
DIR_TOKEN_LENGTH = 6  # bytes, produces 12 hex chars
OWNER_KEY_LENGTH = 16  # bytes, produces 32 hex chars
DIR_DEFAULT_TTL = 10800  # 3 hours
DEFAULT_EXCLUDES = ['.git/', '__pycache__/', '.env', 'node_modules/', '.DS_Store', '*.pyc', '.venv/']
MAX_DIR_FILES = 10000
MAX_RENDER_SIZE = 5 * 1024 * 1024  # 5 MB — files larger than this won't be syntax-highlighted
CLEANUP_INTERVAL = 60  # seconds between auto-stop checks

STATE_DIR = os.path.expanduser('~/.vibefs')
DB_PATH = os.path.join(STATE_DIR, 'vibefs.db')
PID_PATH = os.path.join(STATE_DIR, 'vibefs.pid')
LOG_PATH = os.path.join(STATE_DIR, 'vibefs.log')
CONFIG_PATH = os.path.join(STATE_DIR, 'config.json')


def ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)
