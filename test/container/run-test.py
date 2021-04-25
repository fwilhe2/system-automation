import subprocess
import shutil
import os
from pathlib import Path
import re


def run_ansible(playbook):
    print(f"::group::Running Playbook {playbook}")
    assert (
        subprocess.run(
            ["ansible-playbook", "--skip-tags", "notest", "-vv", playbook]
        ).returncode
        == 0
    )
    # Idempotence check: Run again and verify nothing fails or changes the second time
    # Idea via https://github.com/geerlingguy/mac-dev-playbook/blob/7382e0241fe27cf17fabe31582af0269551e7004/.github/workflows/ci.yml#L71
    rerun = subprocess.run(
        ["ansible-playbook", "--skip-tags", "notest", playbook], capture_output=True
    )
    assert rerun.returncode == 0
    changed_match = re.fullmatch(
        ".*changed=0.*failed=0.*", rerun.stdout.decode("utf-8"), re.DOTALL
    )
    print(changed_match)
    assert changed_match
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
