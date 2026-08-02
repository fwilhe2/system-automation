#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

# ansible.cfg carries the inventory and the role paths, and is only picked up
# from the repository root
cd "$(dirname "$0")/.."

# Everything is the default; a playbook name applies just that half
case "${1:-site}" in
    site) PLAYBOOK=site.yml ;;
    *) PLAYBOOK="playbooks/$1.yml" ;;
esac

ansible-playbook --ask-become-pass "$PLAYBOOK"
