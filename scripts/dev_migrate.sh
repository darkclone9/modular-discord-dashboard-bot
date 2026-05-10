#!/usr/bin/env sh
set -eu
uv run alembic upgrade head
