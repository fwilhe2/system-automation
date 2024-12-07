#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

# This is a workaround for the 'x is being updated by another instance' issue
# https://github.com/mozilla/gecko-dev/blob/6597dd03bad82c891d084eed25cafd0c85fb333e/toolkit/mozapps/update/UpdateService.sys.mjs#L3952

set -o nounset
set -o errexit

ansible-playbook --ask-become-pass --inventory inventory desktop.yml --tags firefox
