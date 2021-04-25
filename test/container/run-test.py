import subprocess

subprocess.run(["bash", "-c", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"])
subprocess.run(["ansible-playbook", "--skip-tags", "notest", "-vv", "/mnt/common.yml"])