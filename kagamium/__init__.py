from __future__ import annotations

from kagamium.bootstrap import ensure_runtime_dependencies, install_runtime_dependencies
from kagamium.config import Settings, load_settings, settings


def create_app(app_settings: Settings | None = None):
    ensure_runtime_dependencies()
    from kagamium.main import create_app as _create_app

    return _create_app(app_settings)


def main() -> None:
    ensure_runtime_dependencies()
    from kagamium.main import main as _main

    _main()


__all__ = [
    "Settings",
    "create_app",
    "ensure_runtime_dependencies",
    "install_runtime_dependencies",
    "load_settings",
    "main",
    "settings",
]
