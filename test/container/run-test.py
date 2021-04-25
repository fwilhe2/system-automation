import subprocess

subprocess.run(["bash", "-c", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"])
assert subprocess.run(["ansible-playbook", "--become-method=su", "--skip-tags", "notest", "-vv", "/home/user/common.yml"]).returncode == 0
