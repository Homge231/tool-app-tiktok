from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIRECTORY_NAME = "NumberTyper"
DATA_DIRECTORY_ENV = "NUMBERTYPER_DATA_DIR"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Return the read-only root that contains bundled application resources."""
    if is_frozen():
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Return the per-user writable data directory for the application."""
    override = os.environ.get(DATA_DIRECTORY_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if not is_frozen():
        return Path.cwd().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return (Path(local_app_data) / APP_DIRECTORY_NAME).resolve()
    return (Path.home() / "AppData" / "Local" / APP_DIRECTORY_NAME).resolve()


def config_directory(explicit_config: str | Path | None = None) -> Path:
    if explicit_config is not None:
        return Path(explicit_config).expanduser().resolve().parent
    return user_data_dir() if is_frozen() else Path.cwd().resolve()


def resolve_model_path(value: str | Path, config_dir: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()

    user_candidate = (config_dir / path).resolve()
    if user_candidate.exists():
        return user_candidate

    bundled_candidate = (resource_root() / path).resolve()
    if bundled_candidate.exists():
        return bundled_candidate

    # Prefer the user-data location for an absent model. This permits a future
    # first-run model installer without writing into the application folder.
    return user_candidate


def resolve_log_directory(value: str | Path, config_dir: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (config_dir / path).resolve()


__all__ = [
    "APP_DIRECTORY_NAME",
    "DATA_DIRECTORY_ENV",
    "config_directory",
    "is_frozen",
    "resolve_log_directory",
    "resolve_model_path",
    "resource_root",
    "user_data_dir",
]
