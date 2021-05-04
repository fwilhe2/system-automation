import subprocess
import os
import re
import sys
import pathlib


def assert_equals(first, second, message):
    if not first == second:
        sys.exit(
            f"Assertion failed. '{first}' should equal '{second}', but did not. Message: {message}"
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


def run_ansible(playbook):
    assert_equals(
        subprocess.run(
            ["ansible-playbook", "--become-method=su", "--skip-tags", "notest", "-vv", playbook]
        ).returncode,
        0,
        f"Expected running playbook '{playbook}' to return exit code 0.",
    )
    # Idempotence check: Run again and verify nothing fails or changes the second time
    # Idea via https://github.com/geerlingguy/mac-dev-playbook/blob/7382e0241fe27cf17fabe31582af0269551e7004/.github/workflows/ci.yml#L71
    rerun = subprocess.run(
        ["ansible-playbook", "--become-method=su", "--skip-tags", "notest", playbook], capture_output=True
    )
    assert_equals(
        rerun.returncode,
        0,
        f"Expected running playbook '{playbook}' (second run) to return exit code 0.",
    )
    rerun_stdout = rerun.stdout.decode("utf-8")
    changed_match = re.fullmatch(".*changed=0.*failed=0.*", rerun_stdout, re.DOTALL)
    print(changed_match)
    assert_not_none(
        changed_match,
        f"Idempotence check failed: Could not find 'changed=0' and 'failed=0' in output:\n{rerun_stdout}",
    )


def print_os_version():
    os_release = pathlib.Path("/etc/os-release").read_text()
    for item in os_release.split("\n"):
        if item.startswith("PRETTY_NAME"):
            print(f"Running on OS: {item.split('=')[1]}")


print_os_version()
run_group(run_ansible, "Running Playbook common", "/home/user/common.yml")
run_group(run_ansible, "Running Playbook desktop", "/home/user/desktop.yml")

# Assertions in set-up system follow here


def assert_system_properties():
    expected_binaries = ["javac", "mvn", "gradle", "go", "keepassxc-cli"]

    expected_binaries_command = {
        "javac": "-version",
        "kotlinc": "-version",
        "mvn": "-version",
        "gradle": "-version",
        "go": "version",
        "keepassxc-cli": "-version",
        "cargo": "--version",
        "topgrade": "--version",
    }

    for binary in expected_binaries:
        for root, _, files in os.walk("/"):
            if binary in files:
                binary_with_path = os.path.join(root, binary)
                print(f"Found binary at '{binary_with_path}'")
                script = f"set -e && source ~/.custom-path.sh && {binary_with_path} {expected_binaries_command[binary]}"
                assert_equals(
                    subprocess.run(["bash", "-c", f"{script}"]).returncode,
                    0,
                    f"Expected {script} to run with exit code 0.",
                )


run_group(assert_system_properties, "Assert Properties of installed System")
