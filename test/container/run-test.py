import subprocess
import shutil
import os
import re
import sys
import pathlib
from stat import *

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


def run_ansible(playbook):
    print(f"::group::Running Playbook {playbook}")
    assert_equals(
        subprocess.run(
            ["ansible-playbook", "--skip-tags", "notest", "-vv", playbook]
        ).returncode,
        0,
        f"Expected running playbook '{playbook}' to return exit code 0.",
    )
    # Idempotence check: Run again and verify nothing fails or changes the second time
    # Idea via https://github.com/geerlingguy/mac-dev-playbook/blob/7382e0241fe27cf17fabe31582af0269551e7004/.github/workflows/ci.yml#L71
    rerun = subprocess.run(
        ["ansible-playbook", "--skip-tags", "notest", playbook], capture_output=True
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
        "Idempotence check failed: Could not find 'changed=0' and 'failed=0' in output:\n{rerun_stdout}",
    )
    print("::endgroup::")


print("::group::Install Rust")
subprocess.run(
    [
        "bash",
        "-c",
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
    ]
)
print("::endgroup::")

run_ansible("/mnt/common.yml")
run_ansible("/mnt/desktop.yml")

# Assertions in set-up system follow here
expected_binaries = ['javac', 'kotlinc', 'mvn', 'gradle', 'go']

print("::group::Assertions")

for binary in expected_binaries:
    for root, dirs, files in os.walk("/"):
        if binary in files:
            binary_with_path = os.path.join(root, binary)
            print(binary_with_path)
            subprocess.run([binary_with_path, '--help'])

print("::endgroup::")
