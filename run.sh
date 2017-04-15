#!/bin/bash

sudo ansible-galaxy install --force -r requirements.yml
ansible-playbook --inventory=inventory common.yml
ansible-playbook --inventory=inventory software-development.yml
