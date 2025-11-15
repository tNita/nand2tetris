#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_TRANSLATOR="$SCRIPT_DIR/vmtranslator.py"
SAMPLE_SRC="$SCRIPT_DIR/sample"

if [[ ! -d "$SAMPLE_SRC" ]]; then
  echo "Sample directory not found: $SAMPLE_SRC" >&2
  exit 1
fi

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

WORK_SAMPLE="$TMP_ROOT/sample"
cp -R "$SAMPLE_SRC" "$WORK_SAMPLE"

for target in "$WORK_SAMPLE"/*; do
  [[ -d "$target" ]] || continue
  python "$VM_TRANSLATOR" "$target"

  base_name="$(basename "$target")"
  generated="$target/$base_name.asm"
  expected="$SAMPLE_SRC/$base_name/$base_name.asm"

  if [[ ! -f "$expected" ]]; then
    echo "Expected file missing: $expected" >&2
    exit 1
  fi

  diff -u "$expected" "$generated"
done

echo "VM translator regression tests passed"
