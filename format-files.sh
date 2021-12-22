#!/bin/bash
set -o nounset
set -o errexit
set -o xtrace

npx prettier --write "./**/*.yml"

yapf --recursive --in-place .
