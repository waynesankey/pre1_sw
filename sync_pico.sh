#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PICO_DIR="$ROOT_DIR/pico"

rm -rf "$PICO_DIR"
mkdir -p "$PICO_DIR/lib" "$PICO_DIR/modules"

cp -f "$ROOT_DIR/main.py" "$ROOT_DIR/config.py" "$ROOT_DIR/selector.json" "$ROOT_DIR/tubeData.csv" "$PICO_DIR/"
if [[ -f "$ROOT_DIR/amp_state.json" ]]; then
  cp -f "$ROOT_DIR/amp_state.json" "$PICO_DIR/"
fi

shopt -s nullglob
for f in "$ROOT_DIR"/lib/*.py; do
  [[ "$(basename "$f")" == "__init__.py" ]] && continue
  cp -f "$f" "$PICO_DIR/lib/"
done

for f in "$ROOT_DIR"/modules/*.py; do
  cp -f "$f" "$PICO_DIR/modules/"
done
