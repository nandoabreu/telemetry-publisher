#!/usr/bin/env bash
source .env

LOG_LEVEL="${LOG_LEVEL:-INFO}"
DEPENDENCIES_DIR="${VIRTUALENV:-$(poetry env info -p 2>/dev/null)}"
PYTHON_VERSION=$(cat .python-version 2>/dev/null || python3 -V | sed "s,.* \(3\.[0-9]\+\)\..*,\1,")
PYTHONPATH="$DEPENDENCIES_DIR/lib/python${PYTHON_VERSION}/site-packages:$DEPENDENCIES_DIR/bin:src"


echo "Start active (pull) collects"
LOG_LEVEL="${LOG_LEVEL}" PYTHONPATH="$PYTHONPATH" python -m app
