#!/bin/bash
# Bestimme das Verzeichnis dieses Skripts und nutze es für relative Pfade
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$DIR/venv/bin/activate"
python3 "$DIR/instantsauger.py"