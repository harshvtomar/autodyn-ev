#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
echo "AutoDyn EV v0.6.0 — Python version:"
python3 --version
echo "Running engineering and HTTP tests..."
python3 -m unittest discover -s tests -q
echo "Open http://127.0.0.1:${1:-8765}/ in your browser"
python3 -m autodyn_ev.server --port "${1:-8765}"
