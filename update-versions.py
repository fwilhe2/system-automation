#!/usr/bin/env python

import yaml

# todo: this script should be able to get the latest versions and update them automated
with open("roles/bin/defaults/main.yml", 'r') as stream:
    try:
        versions = yaml.safe_load(stream)
        for v in versions:
            print(v)
            print(versions[v])
    except yaml.YAMLError as exc:
        print(exc)