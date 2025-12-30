# Centralized Configuration

This folder is the source of truth for local development configuration. Production config and compose live in a separate repo: https://github.com/bee0511/switch-testbed-load-balancer-config

Structure:
- `base/device.yaml`: non-sensitive device inventory mounted to `/app/config` by default (dev use in this repo).
- `backend.env`: backend environment variables for development.
- `frontend.env`: frontend runtime configuration for development (`VITE_API_BASE_URL`).
- `secrets/credentials.yaml.example`: template for SSH credentials; place the real `credentials.yaml` here (gitignored) or manage it with a secrets tool.

Usage (dev only, no fallbacks):
- Copy `secrets/credentials.yaml.example` → `secrets/credentials.yaml` and fill credentials.
- Copy `config/backend.env.example` → `config/backend.env` and set `API_BEARER_TOKEN`.
- Copy `config/frontend.env.example` → `config/frontend.env` and set `VITE_API_BASE_URL`.
- Edit `config/base/device.yaml` as needed.
- Start with `docker compose up --build -d`.
