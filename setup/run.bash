#!/usr/bin/env bash

PYTHON_VERSION=$(python3 -V | sed "s,.* \(3\.[0-9]\+\)\..*,\1,")
[ -z "$VIRTUAL_ENV" ] && VIRTUAL_ENV=.venv/lib/python$PYTHON_VERSION/site-packages
[ ! -d "$VIRTUAL_ENV" ] && VIRTUAL_ENV=dependencies

set -x
PYTHONPATH="$VIRTUAL_ENV:src" python -m app
