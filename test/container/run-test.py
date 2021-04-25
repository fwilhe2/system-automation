import subprocess
import shutil

subprocess.run(["bash", "-c", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"])
subprocess.run(["ansible-playbook", "--skip-tags", "notest", "-vv", "/mnt/common.yml"])

assert shutil.which('mvn') != None
assert shutil.which('javac') != None
assert shutil.which('gradle') != None
assert shutil.which('kotlinc') != None