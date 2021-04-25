import subprocess
import shutil
import os
from pathlib import Path

subprocess.run(
    [
        "bash",
        "-c",
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
    ]
)
assert (
    subprocess.run(
        ["ansible-playbook", "--skip-tags", "notest", "-vv", "/home/user/common.yml"]
    ).returncode
    == 0
)

paths = ['apache-maven-3.8.1', 'gradle-7.0', 'sapmachine-jdk-11.0.10']

for path in paths:
    p = Path.home() / 'software' / path
    assert p.exists()
    assert p.is_dir()


print(os.environ['PATH'])

# assert shutil.which("mvn") is not None
# assert shutil.which("javac") is not None
# assert shutil.which("gradle") is not None
# assert shutil.which("kotlinc") is not None
