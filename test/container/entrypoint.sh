#!/bin/bash -l

set -x
set -o errexit

cat /etc/os-release

id

echo "::group::Install rust (requirement of dotfiles)"
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
echo "::endgroup::"

echo "::group::Run Playbook"
ansible-playbook --become-method=su  --skip-tags notest -vvvv /home/user/common.yml
source ~/.custom-path.sh # Make sure path is updated
source ~/.bashrc
echo "::endgroup::"

echo "::group::Test Installed Commands"
declare -a EXPECTED_COMMANDS=("java" "mvn" "gradle" "go" "kotlinc" "node" "topgrade")
for i in "${EXPECTED_COMMANDS[@]}"
do
    which $i
done
echo "::endgroup::"

# Idempotence check, via https://github.com/geerlingguy/mac-dev-playbook/blob/7382e0241fe27cf17fabe31582af0269551e7004/.github/workflows/ci.yml#L71
echo "::group::Idempotence check"
idempotence=$(mktemp)
ansible-playbook --become-method=su  --skip-tags notest -vvvv /home/user/common.yml | tee -a ${idempotence}
tail ${idempotence} | grep -q 'changed=0.*failed=0' && (echo 'Idempotence test: pass' && exit 0) || (echo 'Idempotence test: fail' && exit 1)
echo "::endgroup::"

echo "::group::Run Desktop Playbook"
ansible-playbook --become-method=su  --skip-tags notest -vvvv /home/user/desktop.yml
echo "::endgroup::"

echo "::group::Check Desktop App Versions"
codium --user-data-dir=/tmp --version
codium --user-data-dir=/tmp --list-extensions
keepassxc-cli --version
echo "::endgroup::"

echo "::group::Idempotence check"
idempotence=$(mktemp)
ansible-playbook --become-method=su  --skip-tags notest -vvvv /home/user/desktop.yml | tee -a ${idempotence}
tail ${idempotence} | grep -q 'changed=0.*failed=0' && (echo 'Idempotence test: pass' && exit 0) || (echo 'Idempotence test: fail' && exit 1)
echo "::endgroup::"