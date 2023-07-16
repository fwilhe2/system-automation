#!/usr/bin/bash
# SPDX-FileCopyrightText: 2022 Maxwell G <gotmax@e.email>
# SPDX-License-Identifier: MIT

set -euo pipefail
ROLE_DIR=$(dirname $(readlink -f ${0}))
TOP_LEVEL=$(dirname $(dirname ${ROLE_DIR}))

args=("$@")
shift
while [ -n "${1-}" ]; do
    if [ "${1}" = "-s" ]; then
        shift
        if [ -d "${ROLE_DIR}/molecule/${1}" ]; then
            TOP_LEVEL=${ROLE_DIR}
            break
        fi
    fi
    shift
done



cd ${TOP_LEVEL}
export CONVERGE_PLAYBOOK="${ROLE_DIR}/example-playbook.yaml"
export ROLE_NAME=$(basename ${ROLE_DIR})
molecule "${args[@]}"
