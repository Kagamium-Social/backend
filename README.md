# Kagamium Backend
This is backend part of Kagamium.

The place where all the magic happens.

## Configuration

Runtime settings are loaded from `config.json` in the project root.
If the file is missing, Kagamium falls back to the defaults defined in `kagamium/config.py`.

Swagger UI is served under `/{api_path}/docs` and the OpenAPI schema under `/{api_path}/openapi.json`.
JWT signing uses `jwt_secret`; set a unique value before running outside of development.
Protected API routes accept only bearer JWTs in the `Authorization: Bearer <token>` header.
The backend still exposes `/register`, `/login`, and `/token` so clients can obtain a JWT.

## Dependencies

Running `python -m kagamium` now checks `requirements.txt` and installs missing runtime dependencies with `pip` automatically.
Set `KAGAMIUM_AUTO_INSTALL=0` if you want to disable the auto-install step.
