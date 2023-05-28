#!/bin/bash
set -o nounset
set -o errexit

# Dev playbook is default
PLAYBOOK="${1:-dev}"

ansible-playbook --ask-become-pass --inventory inventory $PLAYBOOK.yml
