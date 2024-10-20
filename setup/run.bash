#!/usr/bin/env bash

VIRTUAL_ENV=${VIRTUAL_ENV:-$(poetry env info -p 2>/dev/null || find . -type d -name '*venv' -exec realpath {} \;)}

if [ -d "$VIRTUAL_ENV" ]; then
  PACKAGES_DIR="$(find "$VIRTUAL_ENV" -type d -name site-packages | tail -1)"
  DEPENDENCIES="$(realpath "$PACKAGES_DIR")"
  PYTHON_BIN="$VIRTUAL_ENV/bin/python"

else
  DEPENDENCIES=dependencies
  PYTHON_BIN=$(which python3)

fi

eval PYTHONPATH="$DEPENDENCIES:src" "$PYTHON_BIN" -m app
