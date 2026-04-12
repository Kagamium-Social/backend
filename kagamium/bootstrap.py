from __future__ import annotations

import importlib
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

AUTO_INSTALL_ENV_VAR = "KAGAMIUM_AUTO_INSTALL"
AUTO_INSTALL_DISABLED_VALUES = {"0", "false", "no"}
REQUIREMENT_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
PACKAGE_IMPORT_NAME_OVERRIDES = {
    "pydantic-core": "pydantic_core",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _requirements_path() -> Path:
    return _project_root() / "requirements.txt"


def _auto_install_enabled() -> bool:
    raw_value = os.getenv(AUTO_INSTALL_ENV_VAR, "1")
    return raw_value.strip().lower() not in AUTO_INSTALL_DISABLED_VALUES


def _package_name_to_import_name(package_name: str) -> str:
    normalized_name = package_name.lower()
    return PACKAGE_IMPORT_NAME_OVERRIDES.get(normalized_name, normalized_name.replace("-", "_"))


def _read_requirement_packages(requirements_path: Path) -> list[str]:
    packages: list[str] = []

    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        candidate = line.split("#", 1)[0].strip()
        if not candidate or candidate.startswith("-"):
            continue

        match = REQUIREMENT_NAME_PATTERN.match(candidate)
        if match is None:
            continue

        packages.append(match.group(1))

    return packages


def _missing_runtime_packages(requirements_path: Path) -> list[str]:
    missing_packages: list[str] = []

    for package_name in _read_requirement_packages(requirements_path):
        import_name = _package_name_to_import_name(package_name)
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(package_name)

    return missing_packages


def install_runtime_dependencies(requirements_path: Path | None = None) -> None:
    resolved_requirements_path = requirements_path or _requirements_path()
    if not resolved_requirements_path.exists():
        raise FileNotFoundError(f"Could not find requirements file: {resolved_requirements_path}")

    print(f"Installing dependencies from {resolved_requirements_path}...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(resolved_requirements_path),
        ],
        cwd=str(resolved_requirements_path.parent),
    )
    importlib.invalidate_caches()


def ensure_runtime_dependencies(requirements_path: Path | None = None) -> None:
    resolved_requirements_path = requirements_path or _requirements_path()
    if not resolved_requirements_path.exists():
        return

    missing_packages = _missing_runtime_packages(resolved_requirements_path)
    if not missing_packages:
        return

    if not _auto_install_enabled():
        missing = ", ".join(missing_packages)
        raise RuntimeError(
            "Missing runtime dependencies: "
            f"{missing}. Set {AUTO_INSTALL_ENV_VAR}=1 or install them with "
            f"`{sys.executable} -m pip install -r {resolved_requirements_path}`."
        )

    install_runtime_dependencies(resolved_requirements_path)
