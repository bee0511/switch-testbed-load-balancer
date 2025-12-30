#!/bin/sh
set -eu

if [ -z "${VITE_API_BASE_URL:-}" ]; then
  echo "VITE_API_BASE_URL is required but not set." >&2
  exit 1
fi

echo "Injecting API URL: $VITE_API_BASE_URL"
sed -i "s|VITE_API_BASE_URL: \".*\"|VITE_API_BASE_URL: \"$VITE_API_BASE_URL\"|g" /usr/share/nginx/html/index.html

exec "$@"
