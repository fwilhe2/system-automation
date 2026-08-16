# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT
"""Applies the playbooks in a test container and checks the result.

Every playbook is applied twice: the second run must report no changes, which
is the idempotence contract. The assertions about the resulting system live in
assertions.py.
"""

import re
import shutil
import subprocess

import distro

import assertions
from assertions import assert_equals, assert_not_none


def run_group(fn, name, *args):
    print(f"::group::{name}")
    fn(*args)
    print("::endgroup::")


def executable(name):
    """Locate a tool, falling back to where pip installs it for the test user."""
    return shutil.which(name) or f"/home/user/.local/bin/{name}"


def install_ansible_galaxy_dependencies():
    subprocess.run([executable("ansible-galaxy"), "install", "-r", "requirements.yml"])


def run_ansible(playbook):
    command = [
        executable("ansible-playbook"),
        # ansible.cfg points at the inventory for a real machine, which has no
        # credentials to escalate with. The escalation method itself comes from
        # ANSIBLE_BECOME_METHOD, which each Containerfile sets.
        "--inventory",
        "test/container/inventory.yml",
        "--skip-tags",
        "notest",
    ]
    assert_equals(
        subprocess.run(command + ["-vv", playbook]).returncode,
        0,
        f"Expected running playbook '{playbook}' to return exit code 0.",
    )
    # Idempotence check: Run again and verify nothing fails or changes the second time
    # Idea via https://github.com/geerlingguy/mac-dev-playbook/blob/7382e0241fe27cf17fabe31582af0269551e7004/.github/workflows/ci.yml#L71
    rerun = subprocess.run(command + [playbook], capture_output=True)

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
    subprocess.run([executable("ansible-playbook"), "--version"])


def print_os_version():
    print(distro.name(pretty=True))


def print_sbom():
    if distro.id() == 'debian' or distro.id() == 'ubuntu':
        subprocess.run(['dpkg-query', '--list', '--no-pager'])

    if distro.id() == 'centos' or distro.id() == 'fedora' or distro.id() == 'almalinux' or distro.id() == 'rocky':
        subprocess.run(['dnf', '--assumeyes', 'list', 'installed'])

    if 'opensuse' in distro.id():
        subprocess.run(['zypper', 'search', '--installed-only', '--details'])


def main():
    print_ansible_version()
    print_os_version()

    run_group(install_ansible_galaxy_dependencies, "Install Dependencies from Ansible Galaxy")
    run_group(run_ansible, "Running Playbook common", "playbooks/common.yml")
    run_group(run_ansible, "Running Playbook desktop", "playbooks/desktop.yml")
    run_group(print_sbom, "Print SBOM")

    run_group(assertions.assert_system_properties,
              "Assert Properties of Installed System")
    run_group(assertions.assert_rust_toolchain, "Assert Rust Toolchain")
    run_group(assertions.assert_uv_installed, "Assert Uv Installed")
    run_group(assertions.assert_telemetry_opt_out, "Assert Telemetry Opt-Out")
    run_group(assertions.assert_spellcheck_locales, "Assert Spellcheck Locales")
    run_group(assertions.assert_firefox_setup, "Assert Firefox Setup")
    run_group(assertions.assert_libreoffice_locale,
              "Assert LibreOffice Locale")
    run_group(assertions.assert_addon_ids_match_their_xpi,
              "Assert Firefox Add-on IDs")


if __name__ == "__main__":
    main()
