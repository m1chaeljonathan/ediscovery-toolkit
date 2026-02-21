import yaml
from pathlib import Path

_config = None

def load_config(path: str | None = None) -> dict:
    global _config
    if _config is not None and path is None:
        return _config
    config_path = Path(path) if path else Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    if path is None:
        _config = cfg
    return cfg
