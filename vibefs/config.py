import json
import os

from .constants import CONFIG_PATH, ensure_state_dir


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
