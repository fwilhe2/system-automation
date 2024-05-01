#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

tmp_dir=$(mktemp -d -t sysauto-XXXXXXXXXX)
curl --location https://github.com/fwilhe2/system-automation/archive/main.zip -o ${tmp_dir}/sysauto.zip
unzip ${tmp_dir}/sysauto.zip -d ${tmp_dir}/extract
ansible-galaxy install -r ${tmp_dir}/extract/system-automation-main/requirements.yml
ansible-playbook --ask-become-pass --inventory ${tmp_dir}/extract/system-automation-main/inventory ${tmp_dir}/extract/system-automation-main/epel.yml
ansible-playbook --ask-become-pass --inventory ${tmp_dir}/extract/system-automation-main/inventory ${tmp_dir}/extract/system-automation-main/common.yml
