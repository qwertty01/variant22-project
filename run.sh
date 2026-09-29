#!/bin/sh
set -eu
PYTHONPATH=. python3 -m src.main "$@"
