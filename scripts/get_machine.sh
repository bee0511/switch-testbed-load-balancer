#!/usr/bin/env bash
set -euo pipefail

BASE="${DISPATCH_BASE:-http://127.0.0.1:8000}"

VERSION="${1:-"1.0"}"
VENDOR="${2:-cisco}"
MODULE="${3:-c8k}"

RESP="$(curl -sS -f "$BASE/get/$VENDOR/$MODULE/$VERSION")"

SERIAL_NUMBER="$(echo "$RESP" | jq -r '.serial_number')"

echo curl -sS -f -X POST "\"$BASE/release/$SERIAL_NUMBER\""