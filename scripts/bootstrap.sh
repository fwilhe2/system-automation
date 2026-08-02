#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

tmp_dir=$(mktemp -d -t sysauto-XXXXXXXXXX)
curl --location https://github.com/fwilhe2/system-automation/archive/main.zip -o "${tmp_dir}/sysauto.zip"
unzip "${tmp_dir}/sysauto.zip" -d "${tmp_dir}/extract"

# From the checkout root, so ansible.cfg is read and the inventory, the role
# paths and the collection path need no flags
cd "${tmp_dir}/extract/system-automation-main"
ansible-galaxy install -r requirements.yml
ansible-playbook --ask-become-pass playbooks/common.yml
