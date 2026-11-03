#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

if ! command -v javac >/dev/null || ! command -v java >/dev/null; then
  echo "A JDK (javac and java) is required for the regression tests." >&2
  exit 1
fi

"$PYTHON" -m unittest discover -s "$SCRIPT_DIR" -p 'test_*.py' -v
