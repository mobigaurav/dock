#!/usr/bin/env bash
set -euo pipefail
src="${BASH_SOURCE[0]}"
while [ -L "$src" ]; do
  dir="$(cd "$(dirname "$src")" && pwd)"
  src="$(readlink "$src")"
  case "$src" in
    /*) ;;
    *) src="$dir/$src" ;;
  esac
done
script_dir="$(cd "$(dirname "$src")" && pwd)"
ROOT="$(cd "$script_dir/../../../.." && pwd)"
if command -v dock >/dev/null 2>&1; then
  exec dock mcp
fi
export PYTHONPATH="${ROOT}/src"
exec python3 -m dock mcp
