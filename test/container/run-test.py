import subprocess
import shutil
import os
from pathlib import Path
import re

def run_ansible(playbook):
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
    assert(re.match("changed=0.*failed=0", rerun.stdout))

subprocess.run(
    [
        "bash",
        "-c",
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
    ]
)

run_ansible("/mnt/common.yml")
run_ansible("/mnt/desktop.yml")
