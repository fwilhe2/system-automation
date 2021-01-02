#!/bin/bash
set -o nounset
set -o errexit

ansible-playbook --inventory=inventory --ask-become-pass common.yml
# ansible-playbook --inventory=inventory software-development.yml
