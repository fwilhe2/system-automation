#!/bin/bash
set -o nounset
set -o errexit

tmp_dir=$(mktemp -d -t sysauto-XXXXXXXXXX)
curl --location https://github.com/fwilhe2/system-automation/archive/master.zip -o ${tmp_dir}/sysauto.zip
unzip ${tmp_dir}/sysauto.zip -d ${tmp_dir}/extract
ansible-playbook --ask-become-pass --inventory inventory ${tmp_dir}/extract/system-automation-master/common.yml
