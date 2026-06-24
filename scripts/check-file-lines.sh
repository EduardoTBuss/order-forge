#!/usr/bin/env bash
# Enforces maximum file line counts per file type.
# Called by prek; receives staged file paths as arguments.
#
# Thresholds:
#   Python (.py)       → 600 lines
#   TypeScript (.ts/.tsx) → 500 lines
#   Other text files   → 600 lines (default)
#
# Bypass: add "file-size-exception" in the first 5 lines of the file.

set -euo pipefail

PYTHON_HARD_LIMIT=600
FRONTEND_TS_HARD_LIMIT=500
ORCHESTRATOR_TS_HARD_LIMIT=600
DEFAULT_HARD_LIMIT=600

failed=0

for file in "$@"; do
  [[ ! -f "$file" ]] && continue

  lines=$(wc -l < "$file")
  limit=$DEFAULT_HARD_LIMIT

  case "$file" in
    *.py)      limit=$PYTHON_HARD_LIMIT ;;
    orchestrator/*.ts|orchestrator/*.tsx) limit=$ORCHESTRATOR_TS_HARD_LIMIT ;;
    *.ts|*.tsx) limit=$FRONTEND_TS_HARD_LIMIT ;;
  esac

  # Allow explicit exceptions declared in the first 5 lines
  if head -5 "$file" | grep -q 'file-size-exception'; then
    continue
  fi

  # Warn on numbered-suffix anti-pattern (e.g. logic_1.py, Component2.tsx)
  basename=$(basename "$file")
  if [[ "$basename" =~ ^.*[_-][0-9]+\.(py|ts|tsx)$ ]]; then
    echo "⚠  $file: numbered suffix detected — use domain-driven names instead"
  fi

  if (( lines > limit )); then
    echo "❌ $file: $lines lines (limit: $limit)"
    failed=1
  fi
done

if (( failed )); then
  echo ""
  echo "Files exceed the line limit. Options:"
  echo "  1. Split into domain-focused files (see component AGENTS.md / skills)"
  echo "  2. Add '# file-size-exception: <reason>' in the first 5 lines"
  exit 1
fi
