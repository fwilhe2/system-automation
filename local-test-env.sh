#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

usage() {
    cat <<'EOF'
Usage: ./local-test-env.sh [DISTRO[:VERSION]] [ENTRYPOINT]

Builds the test image for DISTRO and runs the test suite in it.

DISTRO defaults to fedora. VERSION defaults to the first value listed below,
and takes the same values as the CI matrix in .github/workflows/main.yml:

  debian      stable, testing, unstable
  ubuntu      latest, rolling, devel
  fedora      latest, rawhide
  el          almalinux:10
  opensuse    tumbleweed, leap:16.0
  archlinux   -- (the image is always archlinux:latest)

ENTRYPOINT replaces the test runner, e.g. bash for an interactive shell.

Examples:
  ./local-test-env.sh                   # fedora:latest, full test suite
  ./local-test-env.sh debian:unstable
  ./local-test-env.sh fedora:rawhide bash
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

SPEC=${1:-fedora}
DISTRO=${SPEC%%:*}
VERSION=''
if [[ "$SPEC" == *:* ]]; then
    VERSION=${SPEC#*:}
fi

# The VERSION build argument is not uniform across the Containerfiles: dpkg and
# el take a full image reference, fedora a bare tag, opensuse a path below
# registry.opensuse.org/opensuse/, and archlinux takes none at all.
case "$DISTRO" in
    debian | ubuntu)
        CONTAINERFILE=Containerfile.dpkg
        case "$DISTRO" in
            debian) BUILD_ARGS=(--build-arg="VERSION=debian:${VERSION:-testing}") ;;
            ubuntu) BUILD_ARGS=(--build-arg="VERSION=ubuntu:${VERSION:-latest}") ;;
        esac
        ;;
    fedora)
        CONTAINERFILE=Containerfile.fedora
        BUILD_ARGS=(--build-arg="VERSION=${VERSION:-latest}")
        ;;
    el)
        CONTAINERFILE=Containerfile.el
        BUILD_ARGS=(--build-arg="VERSION=${VERSION:-almalinux:10}")
        ;;
    opensuse)
        CONTAINERFILE=Containerfile.opensuse
        BUILD_ARGS=(--build-arg="VERSION=${VERSION:-tumbleweed}")
        ;;
    archlinux)
        CONTAINERFILE=Containerfile.archlinux
        BUILD_ARGS=()
        ;;
    *)
        echo "Unknown distro: $DISTRO" >&2
        usage >&2
        exit 1
        ;;
esac

ENTRYPOINT=()
if [[ "$#" -ge 2 ]]; then
    ENTRYPOINT=("--entrypoint=$2")
fi

# Image tags may not contain a colon, which el and opensuse versions do.
TAG="system-automation-$DISTRO${VERSION:+-${VERSION//[^a-zA-Z0-9_.-]/-}}"

CLI=docker
command -v podman >/dev/null 2>&1 && CLI=podman

# None of the images run systemd as pid 1. Under docker, which is what CI uses,
# ansible's systemd module notices that on its own and skips the unit handling
# with a warning. Under podman it does not -- is_chroot() compares / against
# /proc/1/root, which match there -- so it runs systemctl for real and the
# docker role fails with "Service is in unknown state". SYSTEMD_OFFLINE puts
# both runtimes on the same path the CI jobs take.
set -x
$CLI build "${BUILD_ARGS[@]+"${BUILD_ARGS[@]}"}" -t "$TAG" --file "test/container/$CONTAINERFILE" .
$CLI run -it --rm --volume "$PWD:/mnt" --env SYSTEMD_OFFLINE=1 "${ENTRYPOINT[@]+"${ENTRYPOINT[@]}"}" --privileged "$TAG"
