#!/usr/bin/env bash
# Resolve this script even when ~/.cursor/skills/dock is a symlink.
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
  exec dock inbox "$@"
fi
export PYTHONPATH="${ROOT}/src"
exec python3 -m dock inbox "$@"
