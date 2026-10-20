#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export GH_TOKEN="$(gh auth token)"

./.venv/bin/python generate.py

if git diff --quiet -- light.svg dark.svg snake.svg README.md; then
    echo "No profile changes detected."
    exit 0
fi

git add light.svg dark.svg snake.svg README.md
git commit -m "chore: refresh profile stats"
git push origin main

echo "GitHub profile updated."
