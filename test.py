# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

import subprocess
import os
import re
import sys
import pathlib
import shutil
import distro

def print_sbom():
  if distro.id() == 'debian' or distro.id() == 'ubuntu':
    print(subprocess.run(['dpkg-query', '--list', '--no-pager']).stdout)

  if distro.id() == 'centos' or distro.id() == 'fedora' or distro.id() == 'almalinux' or distro.id() == 'rocky':
    print(subprocess.run(['dnf', '--assumeyes', 'list', 'installed']).stdout)


print_sbom()