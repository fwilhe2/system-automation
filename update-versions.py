#!/usr/bin/env python

import yaml
import json
import urllib.request
import urllib.parse

# Fixme: non-trivial cases commented out for now
repos = {
    # "SAP/SapMachine": "JDK_VERSION",
    # "apache/maven": "MAVEN_VERSION",
    "gradle/gradle": "GRADLE_VERSION",
    # "apache/ant": "ANT_VERSION",
    "nodejs/node": "NODE_VERSION",
    # "golang/go": "GO_VERSION",
    "cli/cli": "GH_VERSION",
    "JetBrains/kotlin": "KOTLIN_VERSION",
    # "r-darwish/topgrade": "TOPGRADE_VERSION",
}

# current_versions = {'GRADLE_VERSION': '7.1.0', 'NODE_VERSION': '14.17.1', 'GH_VERSION': '1.11.0', 'KOTLIN_VERSION': '1.5.10'}
current_versions = {}

for r in repos:
    print(r)
    url = f"https://api.github.com/repos/{r}/releases/latest"
    f = urllib.request.urlopen(url)
    tag_name = json.loads(f.read().decode("utf-8"))["tag_name"]
    current_versions[repos.get(r)] = tag_name.removeprefix('v')

print(current_versions)
