#!/bin/bash

sudo ansible-galaxy install --force -r requirements.yml
ansible-playbook -K -i inventory common.yml
ansible-playbook -K -i inventory software-development.yml
