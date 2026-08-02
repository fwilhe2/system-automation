#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit
set -o xtrace

cd "$(dirname "$0")/.."

npx prettier --write "./**/*.yml"
