from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "config.json"
LEGACY_CONFIG_KEY_ALIASES = {
    "instanceMotd": "instance_motd",
    "instanceMascotImage": "instance_mascot_image",
    "instanceMascotName": "instance_mascot_name",
    "backendPort": "backend_port",
    "jwtSecret": "jwt_secret",
    "jwtExpirationMinutes": "jwt_expiration_minutes",
    "hostingLocally": "hosting_locally",
    "testMode": "test_mode",
    "CORSorigins": "cors_origins",
}


def _default_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_jwt_secret() -> str:
    return os.getenv("KAGAMIUM_JWT_SECRET", "change-me-before-production")


@dataclass(slots=True, frozen=True)
class Settings:
    instance_motd: str = "vadim gay"
    instance_mascot_image: str = ""
    instance_mascot_name: str = ""
    backend_port: int = 8000
    api_path: str = "api"
    jwt_secret: str = field(default_factory=_default_jwt_secret)
    jwt_expiration_minutes: int = 60
    test_mode: bool = True
    cors_origins: tuple[str, ...] = ("*",)
    project_root: Path = field(
        default_factory=_default_project_root,
    )

    @property
    def api_prefix(self) -> str:
        normalized_path = self.api_path.strip("/")
        if not normalized_path:
            return ""
        return f"/{normalized_path}"

    @property
    def database_path(self) -> Path:
        return self.project_root / "KagamiHiiragi.db"

    @property
    def uploads_dir(self) -> Path:
        return self.project_root / "uploads"


def _normalize_config_keys(raw_config: dict[str, Any]) -> dict[str, Any]:
    configurable_fields = {
        field_.name for field_ in fields(Settings) if field_.name != "project_root"
    }
    normalized_config: dict[str, Any] = {}
    unknown_keys: list[str] = []

    for raw_key, value in raw_config.items():
        normalized_key = LEGACY_CONFIG_KEY_ALIASES.get(raw_key, raw_key)
        if normalized_key not in configurable_fields:
            unknown_keys.append(raw_key)
            continue
        normalized_config[normalized_key] = value

    if unknown_keys:
        supported_keys = sorted(configurable_fields | set(LEGACY_CONFIG_KEY_ALIASES))
        raise ValueError(
            "Unsupported config keys: "
            f"{', '.join(sorted(unknown_keys))}. "
            f"Supported keys: {', '.join(supported_keys)}."
        )

    return normalized_config


def _validate_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    normalized_config = _normalize_config_keys(raw_config)

    string_fields = (
        "instance_motd",
        "instance_mascot_image",
        "instance_mascot_name",
        "api_path",
        "jwt_secret",
    )
    for field_name in string_fields:
        value = normalized_config.get(field_name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Config field '{field_name}' must be a string.")

    bool_fields = ("hosting_locally", "test_mode")
    for field_name in bool_fields:
        value = normalized_config.get(field_name)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"Config field '{field_name}' must be a boolean.")

    int_fields = ("backend_port", "jwt_expiration_minutes")
    for field_name in int_fields:
        value = normalized_config.get(field_name)
        if value is not None and not isinstance(value, int):
            raise ValueError(f"Config field '{field_name}' must be an integer.")

    cors_origins = normalized_config.get("cors_origins")
    if cors_origins is not None:
        if not isinstance(cors_origins, list) or not all(
            isinstance(origin, str) for origin in cors_origins
        ):
            raise ValueError("Config field 'cors_origins' must be a list of strings.")
        normalized_config["cors_origins"] = tuple(cors_origins)

    return normalized_config


def load_settings(project_root: Path | None = None) -> Settings:
    resolved_project_root = project_root or _default_project_root()
    config_path = resolved_project_root / CONFIG_FILENAME

    if not config_path.exists():
        return Settings(project_root=resolved_project_root)

    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ValueError(f"Config file {config_path} must contain a JSON object.")

    validated_config = _validate_config(raw_config)
    return Settings(project_root=resolved_project_root, **validated_config)


settings = load_settings()
