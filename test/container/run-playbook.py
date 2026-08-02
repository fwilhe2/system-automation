# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

import shutil
import subprocess
import sys

# Convenience script for running playbooks in interactive containers for debugging purposes


def ansible_playbook_executable():
    in_path = shutil.which("ansible-playbook")
    if in_path is None:
        return "/home/user/.local/bin/ansible-playbook"
    return in_path


def playbook_path():
    if len(sys.argv) > 1:
        return f"playbooks/{sys.argv[1]}.yml"
    return "playbooks/common.yml"


subprocess.run([
    ansible_playbook_executable(),
    "--inventory",
    "test/container/inventory.yml",
    # "--skip-tags",
    # "notest",
    "-vv",
    playbook_path(),
])
