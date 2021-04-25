import subprocess
import shutil
import os
from pathlib import Path

def run_ansible(playbook):
    assert (
        subprocess.run(
            ["ansible-playbook", "--skip-tags", "notest", "-vv", playbook]
        ).returncode
        == 0
    )

subprocess.run(
    [
        "bash",
        "-c",
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
    ]
)

run_ansible("/mnt/common.yml")
run_ansible("/mnt/common.yml")
run_ansible("/mnt/common.yml")
run_ansible("/mnt/desktop.yml")
run_ansible("/mnt/desktop.yml")
run_ansible("/mnt/desktop.yml")
