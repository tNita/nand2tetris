#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JACK_ANALYZER="$SCRIPT_DIR/jack_analyzer.py"
SAMPLE_ROOT="$SCRIPT_DIR/sample"

if [[ ! -d "$SAMPLE_ROOT" ]]; then
  echo "Sample directory not found: $SAMPLE_ROOT" >&2
  exit 1
fi

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

status=0

for target in "$SAMPLE_ROOT"/*; do
  [[ -d "$target" ]] || continue
  base_name="$(basename "$target")"
  work_dir="$TMP_ROOT/$base_name"

  cp -R "$target" "$work_dir"

  echo "Processing: $target"
  python "$JACK_ANALYZER" "$work_dir" >/dev/null

  while IFS= read -r expected; do
    rel_path="${expected#"${target}/"}"
    generated="$work_dir/$rel_path"
    if ! diff -u "$expected" "$generated" >"$TMP_ROOT/diff"; then
      echo "Mismatch: $expected" >&2
      cat "$TMP_ROOT/diff" >&2
      status=1
    fi
  done < <(find "$target" -type f -name '*T.xml' | sort)
done

if [[ $status -ne 0 ]]; then
  echo "Sample comparison failed" >&2
  exit 1
fi

echo "All sample outputs match"
