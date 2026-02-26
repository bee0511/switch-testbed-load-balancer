#!/usr/bin/env bash
set -euo pipefail

BASE="${DISPATCH_BASE:-http://127.0.0.1:8000}"
# 1. Path to your .env file
ENV_FILE="config/backend.env"

# 2. Extract the token from the .env file
# This grep/sed combo ignores comments and whitespace to find the exact value
if [ -f "$ENV_FILE" ]; then
    TOKEN=$(grep -v '^#' "$ENV_FILE" | grep 'API_BEARER_TOKEN=' | cut -d '=' -f2- | tr -d '"' | tr -d "'")
else
    echo "Error: $ENV_FILE not found."
    exit 1
fi

if [ -z "$TOKEN" ]; then
    echo "Error: API_BEARER_TOKEN is not set in $ENV_FILE."
    exit 1
fi

echo $TOKEN
# Configuration

VERSION="${1:-"7.1.070"}"
VENDOR="${2:-hp}"
MODULE="${3:-5945}"
# VERSION="${1:-"9.3(13)"}"
# VENDOR="${2:-cisco}"
# MODULE="${3:-n9k}"
RESP="$(curl -sS -X POST \
     -H "Authorization: Bearer $TOKEN" \
     "$BASE/reserve/$VENDOR/$MODULE/$VERSION")"

echo "$RESP" | jq '.'

SERIAL_NUMBER="$(echo "$RESP" | jq -r '.serial')"

if [ "$SERIAL_NUMBER" = "null" ] || [ -z "$SERIAL_NUMBER" ]; then
    echo "No machine reserved."
    exit 1
fi
echo curl -sS -f -X POST -H \"Authorization: Bearer $TOKEN\" "\"$BASE/release/$SERIAL_NUMBER\""