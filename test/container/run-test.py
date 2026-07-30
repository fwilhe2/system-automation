# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

import subprocess
import json
import os
import platform
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

firefox_channels = {
    "devedition": "Firefox Developer",
    "nightly": "Firefox Nightly",
}


def read_from_omni(omni, path):
    # unzip exits 2 on the non-standard headers omni.ja uses, but still extracts
    # the file correctly, so the output is checked instead of the return code.
    result = subprocess.run(["unzip", "-p", str(omni), path], capture_output=True)
    assert_true(
        len(result.stdout) > 0,
        f"Expected to read '{path}' from '{omni}': {result.stderr.decode('utf-8')}",
    )
    return result.stdout.decode("utf-8")


def javascript_string_list(source, name):
    """Read a `const name = ["a", "b"];` array out of a Firefox module."""
    match = re.search(rf"(?:const|let)\s+{name}\s*=\s*\[(.*?)\];", source, re.DOTALL)
    assert_not_none(
        match,
        f"Could not find '{name}' in Policies.sys.mjs. Firefox likely restructured "
        f"the preference allow list and this test needs to be updated.",
    )
    return re.findall(r'"([^"]+)"', match.group(1))


def elf_machine(binary):
    """Read e_machine out of an ELF header, without needing 'file' installed."""
    with open(binary, "rb") as elf:
        header = elf.read(20)
    assert_equals(header[:4], b"\x7fELF", f"Expected '{binary}' to be an ELF binary.")
    return int.from_bytes(header[18:20], "little")


def assert_firefox_setup():
    home = pathlib.Path.home()
    # https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html
    expected_machine = {"x86_64": 0x3E, "aarch64": 0xB7}[platform.machine()]

    for channel, display_name in firefox_channels.items():
        install = pathlib.Path(f"/opt/firefox/firefox-{channel}/firefox")

        # Mozilla serves x86_64 unless the download URL asks for another
        # architecture, so a wrong URL yields a browser that cannot run here.
        assert_equals(
            elf_machine(install / "firefox"), expected_machine,
            f"{display_name} was built for a different architecture than "
            f"{platform.machine()}. Check the os= parameter of the download URL.")

        # Firefox opens the profile manager and waits forever when the --profile
        # directory does not exist, so its presence is what makes the browser
        # start unattended.
        profile = home / ".local/share/firefox-profiles" / channel
        assert_true(profile.is_dir(),
                    f"Expected profile directory '{profile}' for {display_name}.")
        assert_equals(
            oct(profile.stat().st_mode & 0o777), oct(0o700),
            f"Expected profile directory '{profile}' to be private.")

        entry = home / ".local/share/applications" / f"firefox-{channel}.desktop"
        assert_true(entry.is_file(),
                    f"Expected desktop entry '{entry}' for {display_name}.")
        exec_lines = [
            line for line in entry.read_text().splitlines()
            if line.startswith("Exec=")
        ]
        assert_true(len(exec_lines) > 0, f"Expected an Exec line in '{entry}'.")
        for exec_line in exec_lines:
            assert_true(
                f"--profile {profile}" in exec_line,
                f"Expected '{exec_line}' to start on profile '{profile}'.")
            # Opening in a private window is intentional for these channels.
            assert_true(" --private-window " in exec_line,
                        f"Expected '{exec_line}' to open a private window.")
            binary = pathlib.Path(exec_line.split(" ")[2])
            assert_true(os.access(binary, os.X_OK),
                        f"Expected '{binary}' from '{entry}' to be executable.")

        # Validate the generated policies against the rules of the very Firefox
        # build that was just installed, so this keeps working as Firefox
        # changes which policies and preferences it accepts.
        policies = json.loads(
            (install / "distribution/policies.json").read_text())["policies"]
        omni = install / "browser/omni.ja"

        schema = json.loads(
            read_from_omni(omni, "modules/policies/policies-schema.json"))
        for policy in policies:
            assert_true(
                policy in schema["properties"],
                f"'{policy}' is not a policy {display_name} knows about.")

        source = read_from_omni(omni, "modules/policies/Policies.sys.mjs")
        allowed_prefixes = javascript_string_list(source, "allowedPrefixes")
        allowed_security_prefs = javascript_string_list(source,
                                                        "allowedSecurityPrefs")
        blocked_prefs = javascript_string_list(source, "blockedPrefs")

        # Firefox silently drops preferences it does not allow, and only reports
        # them in about:policies, so they have to be checked up front.
        for preference in policies.get("Preferences", {}):
            if preference.startswith("security."):
                allowed = preference in allowed_security_prefs
            else:
                allowed = any(
                    preference.startswith(prefix)
                    for prefix in allowed_prefixes)
            assert_true(
                allowed and preference not in blocked_prefs,
                f"{display_name} refuses to set '{preference}' via the "
                f"Preferences policy. Use the dedicated policy for it instead.")

        print(f"{display_name}: profile, desktop entry and "
              f"{len(policies)} policies are valid")


run_group(assert_firefox_setup, "Assert Firefox Setup")
