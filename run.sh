#!/bin/bash
set -o nounset
set -o errexit

ansible-playbook --inventory=inventory common.yml
ansible-playbook --inventory=inventory software-development.yml
