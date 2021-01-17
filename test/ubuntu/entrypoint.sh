#!/bin/bash -l

set -x

echo "::group::Run Playbook"
ansible-playbook -vv /mnt/common.yml
source ~/.custom-path.sh # Make sure path is updated
echo "::endgroup::"

echo "::group::Test Installed Commands"
declare -a EXPECTED_COMMANDS=("java" "mvn" "gradle" "go" "kotlinc" "node")
for i in "${arr[@]}"
do
    if ! [ -x "$(command -v $i)" ]; then
        echo "Error: Expected $i to be installed." >&2
        exit 1
    fi
done
echo "::endgroup::"
