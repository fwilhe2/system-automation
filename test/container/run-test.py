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
    # Idempotence check
    rerun = subprocess.run(
        ["ansible-playbook", "--skip-tags", "notest", "-vv", playbook], capture_output=True
    )
    assert(rerun.returncode == 0)

    # debug
    print(rerun.stdout.decode("utf-8"))
    
    assert(re.match(".*changed=0.*failed=0.*", rerun.stdout.decode("utf-8")))
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
