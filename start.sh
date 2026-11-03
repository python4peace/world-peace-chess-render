#!/bin/sh
set -eu
exec gunicorn --worker-class gthread --workers 1 --threads 8 \
  --bind "0.0.0.0:${PORT:-10000}" --timeout 120 \
  --access-logfile - --error-logfile - app:app
