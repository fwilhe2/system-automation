#!/bin/bash
set -o nounset
set -o errexit

DISTRO=fedora

if [[ "$#" -eq 1 ]]; then
    DISTRO=$1
fi

CLI=docker

command -v podman >/dev/null 2>&1 && CLI=podman

$CLI build --build-arg=VERSION=latest -t system-automation-$DISTRO --file test/container/Containerfile.$DISTRO .
$CLI run -it --rm --entrypoint=bash --volume $PWD:/mnt --privileged system-automation-$DISTRO
