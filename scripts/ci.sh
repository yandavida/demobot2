#!/usr/bin/env bash
set -euo pipefail

banner() {
  echo
  echo "==================== $1 ===================="
}

banner "Ruff lint (ruff check .)"
ruff check .

banner "Type check (mypy)"
mypy

banner "Tests (pytest -q)"
pytest -q
