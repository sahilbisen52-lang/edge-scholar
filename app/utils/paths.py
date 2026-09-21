"""Centralized path resolution for EdgeScholar."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def get_app_root() -> Path:
    """Return the root directory of the edge-scholar project."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return here.parent.parent.parent  # fallback


def get_data_dir() -> Path:
    """
    Return the local data directory.
    Prefers environment variable EDGESCHOLAR_DATA_DIR or project-local data/ directory
    for portable, offline, self-contained execution without polluting system folders.
    """
    env_dir = os.environ.get("EDGESCHOLAR_DATA_DIR")
    if env_dir:
        return Path(env_dir)

    project_data = get_app_root() / "data"
    if project_data.exists():
        return project_data

    # Windows production fallback
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "EdgeScholar" / "data"

    # Default to project data directory
    return project_data


def get_config_dir() -> Path:
    """Return the configuration directory."""
    env_dir = os.environ.get("EDGESCHOLAR_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    # Keep config inside data directory or app root for isolation
    return get_data_dir() / "config"


def get_models_dir() -> Path:
    return get_app_root() / "models"


def get_fixtures_dir() -> Path:
    return get_app_root() / "tests" / "fixtures"
