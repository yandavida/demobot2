#!/usr/bin/env bash
set -euo pipefail

banner() {
  echo
  echo "==================== $1 ===================="
}

banner "Ruff lint (ruff check .)"
ruff check .

banner "Type check (mypy: PortfolioEngine V2 only)"
mypy \
  core/adapters \
  core/portfolio/models.py \
  core/portfolio/engine.py \
  core/portfolio/cache.py \
  core/fx/contracts.py

banner "Tests (pytest -q)"
pytest -q
