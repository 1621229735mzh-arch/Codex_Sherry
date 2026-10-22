"""Resolve optional work-pets tooling without a machine-specific install path."""
import os
from pathlib import Path


def skill_scripts(explicit=None):
    configured = explicit or os.environ.get("WORK_PETS_SCRIPT_DIR")
    if configured:
        result = Path(configured).expanduser().resolve()
        if not (result / "validate_atlas.py").is_file():
            raise SystemExit(f"Not a work-pets scripts directory: {result}")
        return result
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    candidates = list(codex_home.glob("plugins/cache/*/work-pets/*/skills/create-pet/scripts"))
    candidates = [p for p in candidates if (p / "validate_atlas.py").is_file()]
    if not candidates:
        raise SystemExit("Install work-pets or pass --skill-dir /path/to/create-pet/scripts")
    return max(candidates, key=lambda p: p.stat().st_mtime)
