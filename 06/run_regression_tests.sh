#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSEMBLER="$SCRIPT_DIR/assembler.py"
SAMPLE_SRC="$SCRIPT_DIR/sample"

if [[ ! -d "$SAMPLE_SRC" ]]; then
  echo "Sample directory not found: $SAMPLE_SRC" >&2
  exit 1
fi

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

WORK_SAMPLE="$TMP_ROOT/sample"
cp -R "$SAMPLE_SRC" "$WORK_SAMPLE"

find "$WORK_SAMPLE" -type f -name '*.hack' -delete

for asm in "$WORK_SAMPLE"/*.asm; do
  [[ -f "$asm" ]] || continue
  python "$ASSEMBLER" "$asm"
done

for expected in "$SAMPLE_SRC"/*.hack; do
  [[ -f "$expected" ]] || continue
  generated="$WORK_SAMPLE/$(basename "$expected")"
  if [[ ! -f "$generated" ]]; then
    echo "Missing generated file: $generated" >&2
    exit 1
  fi
  diff -u "$expected" "$generated"
done

echo "Assembler regression tests passed"
