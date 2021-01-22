#!/bin/bash -l

set -x
set -o errexit

echo "::group::Run Playbook"
ansible-playbook -vv /mnt/common.yml
source ~/.custom-path.sh # Make sure path is updated
echo "::endgroup::"

echo "::group::Test Installed Commands"
declare -a EXPECTED_COMMANDS=("java" "mvn" "gradle" "go" "kotlinc" "node")
for i in "${EXPECTED_COMMANDS[@]}"
do
    which $i
done
echo "::endgroup::"
