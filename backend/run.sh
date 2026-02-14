#!/bin/sh
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
