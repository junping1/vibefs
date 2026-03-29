import json
import os
import secrets

from .constants import CONFIG_PATH, OWNER_KEY_LENGTH, ensure_state_dir


def load_config():
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(cfg):
    ensure_state_dir()
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=2)
        f.write('\n')
    # Restrict permissions: config contains owner_key
    os.chmod(CONFIG_PATH, 0o600)


def get_owner_key():
    """Get the owner key, auto-generating one if it doesn't exist."""
    cfg = load_config()
    key = cfg.get('owner_key')
    if not key:
        key = secrets.token_hex(OWNER_KEY_LENGTH)
        cfg['owner_key'] = key
        save_config(cfg)
    return key
