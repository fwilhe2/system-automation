#!/usr/bin/env python3

import json
from urllib.request import urlopen

# Update once a new Fedora release is out
FEDORA_VERSION = '44'


RELEASES_URL = 'https://gitlab.com/fedora/websites-apps/fedora-websites/fedora-websites-3.0/-/raw/develop/public/releases.json'
OUTPUT_FILE = 'lima_fedora.yaml'

TEMPLATE = """# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: Apache-2.0

# Based on the examples by Akihiro Suda and the lima contributors, see https://github.com/lima-vm/lima, distributed under Apache-2.0 license


images:
- location: "{url_x86_64}"
  arch: "x86_64"
  digest: "sha256:{sha_x86_64}"
- location: "{url_aarch64}"
  arch: "aarch64"
  digest: "sha256:{sha_aarch64}"

ssh:
  localPort: 60033

mounts:
- location: "~"
- location: "/tmp/lima"
  writable: true

provision:
- mode: system
  script: |
    #!/bin/bash
    set -eux -o pipefail
    dnf install -y ansible curl bash unzip

containerd:
  system: false
  user: false

mountTypesUnsupported: [9p]
"""

def fetch_releases(url):
    """Fetches and parses the JSON release data."""
    with urlopen(url) as response:
        return json.load(response)

def find_release_info(versions, arch, version=FEDORA_VERSION):
    """Filters the list for a specific architecture and returns the record."""
    matches = [
        v for v in versions
        if v['version'] == version
        and v['arch'] == arch
        and v['variant'] == 'Cloud'
        and v['subvariant'] == 'Cloud_Base'
        and v['link'].endswith('qcow2')
    ]

    if len(matches) != 1:
        raise RuntimeError(f"Expected 1 match for {arch} v{version}, found {len(matches)}")

    return matches[0]

def main():
    releases = fetch_releases(RELEASES_URL)

    # Get data for both architectures efficiently
    x86_data = find_release_info(releases, 'x86_64')
    arm_data = find_release_info(releases, 'aarch64')

    # Map data into the template
    manifest = TEMPLATE.format(
        url_x86_64=x86_data['link'],
        sha_x86_64=x86_data['sha256'],
        url_aarch64=arm_data['link'],
        sha_aarch64=arm_data['sha256']
    )

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(manifest)

    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()