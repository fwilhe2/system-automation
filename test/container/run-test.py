# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

import subprocess
import os
import re
import sys
import pathlib
import shutil
import distro


def assert_equals(first, second, message):
    if not first == second:
        sys.exit(
            f"Assertion failed. '{first}' should equal '{second}', but did not. Message: {message}"
        )


def assert_true(val, message):
    if val == False:
        sys.exit(
            f"Assertion failed. '{val}' should equal 'True', but did not. Message: {message}"
        )


def assert_not_none(value, message):
    if value is None:
        sys.exit(
            f"Assertion failed. '{value}' should not be 'None'. Message: {message}"
        )


def run_group(fn, name, *args):
    print(f"::group::{name}")
    fn(*args)
    print("::endgroup::")

def install_ansible_galaxy_dependencies():
    subprocess.run([ansible_galaxy_executable(), 'install', '-r', '/home/user/requirements.yml'])

def run_ansible(playbook):
    assert_equals(
        subprocess.run([
            ansible_playbook_executable(),
            "--become-method=su",
            "--skip-tags",
            "notest",
            "-vv",
            playbook,
        ]).returncode,
        0,
        f"Expected running playbook '{playbook}' to return exit code 0.",
    )
    # Idempotence check: Run again and verify nothing fails or changes the second time
    # Idea via https://github.com/geerlingguy/mac-dev-playbook/blob/7382e0241fe27cf17fabe31582af0269551e7004/.github/workflows/ci.yml#L71
    rerun = subprocess.run(
        [
            ansible_playbook_executable(),
            "--become-method=su",
            "--skip-tags",
            "notest",
            playbook,
        ],
        capture_output=True,
    )

    rerun_stdout = rerun.stdout.decode("utf-8")
    rerun_stderr = rerun.stderr.decode("utf-8")
    assert_equals(
        rerun.returncode,
        0,
        f"Expected running playbook '{playbook}' (second run) to return exit code 0.\n{rerun_stdout}\n{rerun_stderr}",
    )
    changed_match = re.fullmatch(".*changed=0.*failed=0.*", rerun_stdout,
                                 re.DOTALL)
    print(changed_match)
    assert_not_none(
        changed_match,
        f"Idempotence check failed: Could not find 'changed=0' and 'failed=0' in output:\n{rerun_stdout}",
    )


def print_ansible_version():
    subprocess.run([ansible_playbook_executable(), "--version"])


def ansible_playbook_executable():
    in_path = shutil.which("ansible-playbook")
    if in_path == None:
        return "/home/user/.local/bin/ansible-playbook"
    return in_path

def ansible_galaxy_executable():
    in_path = shutil.which("ansible-galaxy")
    if in_path == None:
        return "/home/user/.local/bin/ansible-galaxy"
    return in_path

def print_os_version():
    print(distro.name(pretty=True))


def print_sbom():
  if distro.id() == 'debian' or distro.id() == 'ubuntu':
    subprocess.run(['dpkg-query', '--list', '--no-pager'])

  if distro.id() == 'centos' or distro.id() == 'fedora' or distro.id() == 'almalinux' or distro.id() == 'rocky':
    subprocess.run(['dnf', '--assumeyes', 'list', 'installed'])

  if 'opensuse' in distro.id():
    subprocess.run(['zypper', 'search', '--installed-only', '--details'])

print_ansible_version()
print_os_version()
run_group(install_ansible_galaxy_dependencies, "Install Dependencies from Ansible Galaxy")
run_group(run_ansible, "Running Playbook EPEL", "/home/user/epel.yml")
run_group(run_ansible, "Running Playbook Snap", "/home/user/snap.yml")
run_group(run_ansible, "Running Playbook common", "/home/user/common.yml")
run_group(run_ansible, "Running Playbook desktop", "/home/user/desktop.yml")
run_group(print_sbom, "Print SBOM")


# Assertions in set-up system follow here


def assert_system_properties():
    expected_binaries = ["javac", "mvn", "go", "keepassxc-cli"]

    expected_binaries_command = {
        "javac": "-version",
        "mvn": "-version",
        "go": "version",
        "keepassxc-cli": "-version",
        "cargo": "--version",
        "topgrade": "--version",
        "limactl": "--version",
        "qemu-system-x86_64": "--version",
    }

    for binary in expected_binaries:
        binary_with_path = shutil.which(binary)
        if binary_with_path == None:
            sys.exit(f"Error: Could not find {binary}")
        print(f"Found binary for {binary} at '{binary_with_path}'")
        script = f"set -e && {binary_with_path} {expected_binaries_command[binary]}"
        assert_equals(
            subprocess.run(["bash", "-c", f"{script}"]).returncode,
            0,
            f"Expected {script} to run with exit code 0.",
        )

run_group(assert_system_properties, "Assert Properties of Installed System")
