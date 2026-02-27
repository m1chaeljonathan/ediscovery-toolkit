import os
import yaml
from pathlib import Path

_config = None

_DEFAULT_CONFIG = {
    'llm': {
        'base_url': 'http://localhost:11434/v1',
        'model': 'llama3.1:8b',
        'api_key': 'local',
    },
    'server': {
        'upload_dir': './uploads',
        'report_dir': './reports/output',
        'max_file_size_mb': 500,
    },
    'parsing': {
        'encodings': ['utf-8-sig', 'windows-1252'],
    },
}


def _config_path() -> Path:
    return Path(__file__).parent / "config.yaml"


def load_config(path: str | None = None) -> dict:
    global _config
    if _config is not None and path is None:
        return _config

    config_path = Path(path) if path else _config_path()
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    # Merge defaults for any missing sections
    for section, defaults in _DEFAULT_CONFIG.items():
        if section not in cfg:
            cfg[section] = dict(defaults)
        elif isinstance(defaults, dict):
            for key, val in defaults.items():
                cfg[section].setdefault(key, val)

    # Environment variable overrides (Docker / CI)
    if os.environ.get('EDISCOVERY_LLM_URL'):
        cfg['llm']['base_url'] = os.environ['EDISCOVERY_LLM_URL']
    if os.environ.get('EDISCOVERY_LLM_MODEL'):
        cfg['llm']['model'] = os.environ['EDISCOVERY_LLM_MODEL']
    if os.environ.get('EDISCOVERY_LLM_API_KEY'):
        cfg['llm']['api_key'] = os.environ['EDISCOVERY_LLM_API_KEY']

    if path is None:
        _config = cfg
    return cfg


def save_config(cfg: dict) -> None:
    """Persist config to config.yaml and update cached config."""
    global _config
    with open(_config_path(), 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
    _config = cfg


def is_setup_complete() -> bool:
    """Check if first-run setup has been completed."""
    cfg = load_config()
    return cfg.get('setup_complete', False)


def reload_config() -> dict:
    """Force reload config from disk (clears cache)."""
    global _config
    _config = None
    return load_config()
