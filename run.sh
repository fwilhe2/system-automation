#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

# With --uvx, ansible-core is supplied by an ephemeral uv environment instead of
# being installed on the host, and the collections from requirements.yml go to a
# gitignored directory in the repo rather than to ~/.ansible/collections. Python
# is still required on the host either way: that is how ansible modules execute.
UVX=false
if [ "${1:-}" = "--uvx" ]; then
  UVX=true
  shift
fi

# Common playbook is default
PLAYBOOK="${1:-common}"

if [ "$UVX" = true ]; then
  # Pinned rather than floating, so a release cannot change what runs against
  # the machine mid-session. Bump deliberately.
  ANSIBLE_CORE_VERSION="2.21.2"
  COLLECTIONS_PATH="$PWD/.ansible-deps/collections"

  # Only on the first run; delete .ansible-deps to force a refresh.
  # ANSIBLE_COLLECTIONS_PATH has to be set for the install too, not just the
  # playbook: otherwise ansible-galaxy sees a copy in ~/.ansible/collections,
  # decides there is nothing to do and leaves the target directory empty.
  if [ ! -d "$COLLECTIONS_PATH/ansible_collections/community/general" ]; then
    ANSIBLE_COLLECTIONS_PATH="$COLLECTIONS_PATH" \
      uvx --from "ansible-core==$ANSIBLE_CORE_VERSION" \
      ansible-galaxy collection install -r requirements.yml -p "$COLLECTIONS_PATH"
  fi

  ANSIBLE_COLLECTIONS_PATH="$COLLECTIONS_PATH" \
    uvx --from "ansible-core==$ANSIBLE_CORE_VERSION" \
    ansible-playbook --ask-become-pass --inventory inventory "$PLAYBOOK.yml"
else
  ansible-playbook --ask-become-pass --inventory inventory $PLAYBOOK.yml
fi
