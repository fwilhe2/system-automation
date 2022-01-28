#!/bin/bash
set -o nounset
set -o errexit
set -x

DISTRO=fedora
if [[ "$#" -ge 1 ]]; then
    DISTRO=$1
fi

ENTRYPOINT=''
if [[ "$#" -ge 2 ]]; then
    ENTRYPOINT="--entrypoint=$2"
fi

CLI=docker

command -v podman >/dev/null 2>&1 && CLI=podman

$CLI build --build-arg=VERSION=latest -t system-automation-$DISTRO --file test/container/Containerfile.$DISTRO .
$CLI run -it --rm --volume $PWD:/mnt $ENTRYPOINT --privileged system-automation-$DISTRO
