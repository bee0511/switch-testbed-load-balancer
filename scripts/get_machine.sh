#!/usr/bin/env bash
set -euo pipefail

BASE="${DISPATCH_BASE:-http://127.0.0.1:8000}"

VERSION="${1:-"17.09.05e"}"
VENDOR="${2:-cisco}"
MODULE="${3:-c8k}"
RESP="$(curl -sS -X POST "$BASE/reserve/$VENDOR/$MODULE/$VERSION")"

echo "$RESP" | jq '.'

SERIAL_NUMBER="$(echo "$RESP" | jq -r '.serial')"

if [ "$SERIAL_NUMBER" = "null" ] || [ -z "$SERIAL_NUMBER" ]; then
    echo "No machine reserved."
    exit 1
fi
echo curl -sS -f -X POST "\"$BASE/release/$SERIAL_NUMBER\""