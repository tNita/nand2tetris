#!/usr/bin/env bash
set -euo pipefail

for dir in sample/*; do
    python vmtranslator.py "$dir"
done