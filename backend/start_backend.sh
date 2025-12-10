#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
export PYTHONPATH=.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
