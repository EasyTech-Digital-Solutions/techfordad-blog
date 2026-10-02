#!/usr/bin/env bash
# One command to run the test suite. Creates .venv on first use.
#
#   tests/run.sh                  everything that works offline (about 17 minutes: loads every page in Chrome)
#   tests/run.sh --quick          one page of each kind (about 2 minutes): a fast check while you work
#   tests/run.sh tests/test_security.py tests/test_links.py     only some files (these are instant)
#   tests/run.sh --live           also check the published site (run this after merging to main)
#   tests/run.sh --update-baseline tests/test_ui_a11y.py        re-record accessibility known issues (review the diff!)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip -q install -r tests/requirements.txt
exec ./.venv/bin/python -m pytest "$@"
