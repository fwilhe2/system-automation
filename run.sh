#!/bin/bash
set -o nounset
set -o errexit

ansible-playbook --ask-become-pass --inventory inventory common.yml
