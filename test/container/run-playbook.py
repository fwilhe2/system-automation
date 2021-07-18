import shutil
import subprocess
import sys

# Convenience script for running playbooks in interactive containers for debugging purposes


def ansible_playbook_executable():
    in_path = shutil.which("ansible-playbook")
    if in_path == None:
        return "/home/user/.local/bin/ansible-playbook"
    return in_path


def playbook_path():
    if len(sys.argv) > 1:
        return f"/home/user/{sys.argv[1]}.yml"
    return "/home/user/common.yml"


subprocess.run(
    [
        ansible_playbook_executable(),
        "--become-method=su",
        # "--skip-tags",
        # "notest",
        "-vv",
        playbook_path(),
    ]
)