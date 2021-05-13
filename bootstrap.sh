#!/bin/bash
set -o nounset
set -o errexit

if [ -e "/usr/bin/apt-get" ] ; then
    sudo -y apt-get update && sudo -y apt-get upgrade && sudo apt-get -y install ansible curl bash unzip
elif [ -e "/usr/bin/dnf" ] ; then
    sudo dnf -y upgrade && sudo dnf install -y ansible curl bash unzip
fi

tmp_dir=$(mktemp -d -t sysauto-XXXXXXXXXX)
curl --location https://github.com/fwilhe2/system-automation/archive/master.zip -o ${tmp_dir}/sysauto.zip
unzip ${tmp_dir}/sysauto.zip -d ${tmp_dir}/extract
ansible-playbook --ask-become-pass --inventory ${tmp_dir}/extract/system-automation-master/inventory ${tmp_dir}/extract/system-automation-master/common.yml
