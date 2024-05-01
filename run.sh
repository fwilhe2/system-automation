#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

# Common playbook is default
PLAYBOOK="${1:-common}"

ansible-playbook --ask-become-pass --inventory inventory $PLAYBOOK.yml
