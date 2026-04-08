import json
import os
import secrets

from .constants import CONFIG_PATH, OWNER_KEY_LENGTH, ensure_state_dir

_config_cache = None
_config_mtime = 0


def load_config():
    """Load config with mtime-based caching. Rereads only when file changes."""
    global _config_cache, _config_mtime
    if not os.path.isfile(CONFIG_PATH):
        _config_cache = {}
        _config_mtime = 0
        return {}
    mtime = os.path.getmtime(CONFIG_PATH)
    if _config_cache is not None and mtime == _config_mtime:
        return _config_cache
    with open(CONFIG_PATH) as f:
        _config_cache = json.load(f)
    _config_mtime = mtime
    return _config_cache


def save_config(cfg):
    global _config_cache, _config_mtime
    ensure_state_dir()
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=2)
        f.write('\n')
    # Restrict permissions: config contains owner_key
    os.chmod(CONFIG_PATH, 0o600)
    # Invalidate cache so next load_config() picks up changes
    _config_cache = None
    _config_mtime = 0


def get_owner_key():
    """Get the owner key, auto-generating one if it doesn't exist."""
    cfg = load_config()
    key = cfg.get('owner_key')
    if not key:
        key = secrets.token_hex(OWNER_KEY_LENGTH)
        cfg['owner_key'] = key
        save_config(cfg)
    return key
