#!/bin/bash
set -o nounset
set -o xtrace

npx prettier --write "./**/*.yml"

command -v yapf3 >/dev/null 2>&1 && yapf3 --recursive --in-place .
command -v yapf >/dev/null 2>&1 && yapf --recursive --in-place .
