#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

# Usage: run.sh [--keep-going] [site|common|desktop] [ansible-playbook args...]
#
#   ./scripts/run.sh                                  everything
#   ./scripts/run.sh desktop --skip-tags firefox      opt out of a role
#   ./scripts/run.sh --skip-tags upstream             opt out of a whole group
#   ./scripts/run.sh --keep-going                     one role at a time; a failing
#                                                     role does not stop the rest
#
# The tags are listed in README.adoc.

set -o nounset
set -o errexit
set -o pipefail

# ansible.cfg carries the inventory and the role paths, and is only picked up
# from the repository root
cd "$(dirname "$0")/.."

KEEP_GOING=false
if [[ "${1:-}" == --keep-going ]]; then
    KEEP_GOING=true
    shift
fi

# Everything is the default; a playbook name applies just that half. Anything
# starting with a dash is left for ansible-playbook.
PLAYBOOK=site
if [[ $# -gt 0 && "$1" != -* ]]; then
    PLAYBOOK=$1
    shift
fi
case "$PLAYBOOK" in
    site) PLAYBOOKS=(playbooks/common.yml playbooks/desktop.yml) ;;
    *) PLAYBOOKS=("playbooks/$PLAYBOOK.yml") ;;
esac

if [[ "$KEEP_GOING" == false ]]; then
    if [[ "$PLAYBOOK" == site ]]; then
        exec ansible-playbook --ask-become-pass site.yml "$@"
    fi
    exec ansible-playbook --ask-become-pass "${PLAYBOOKS[0]}" "$@"
fi

# One ansible-playbook run per role, selected by the role's first tag, in the
# order the playbooks list them. Ask for the password once and hand it to each
# run through a pipe, so it never touches the disk.
#
# The password is checked once up front, the way sudo does it: three tries,
# then stop. Otherwise a typo fails every privileged role in turn, each one a
# rejected sudo attempt that counts towards pam_faillock's lockout.
for try in 1 2 3; do
    read -r -s -p "BECOME password: " BECOME_PASSWORD
    echo
    if printf '%s\n' "$BECOME_PASSWORD" |
        ansible all --become --become-password-file - \
            -m ansible.builtin.command -a true >/dev/null 2>&1; then
        break
    fi
    if [[ $try -eq 3 ]]; then
        echo "Privilege escalation failed three times, giving up." >&2
        exit 1
    fi
    echo "Sorry, try again." >&2
done

FAILED=()
# fd 3, so ansible-playbook cannot read the list from its stdin
while read -r -u 3 playbook tag; do
    echo "=== $tag ($playbook)"
    # `-` reads the password from stdin. A <(...) path does not work: ansible
    # resolves it to /proc/<pid>/fd/pipe:[...] before opening it.
    if ! printf '%s\n' "$BECOME_PASSWORD" |
        ansible-playbook "$playbook" --tags "$tag" --become-password-file - "$@"; then
        FAILED+=("$tag")
    fi
done 3< <(python3 scripts/tags.py roles "${PLAYBOOKS[@]}")

if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo "Failed: ${FAILED[*]}" >&2
    echo "Rerun one with --tags <name>, or skip them with --skip-tags $(IFS=,; echo "${FAILED[*]}")" >&2
    exit 1
fi
echo "All roles applied."
