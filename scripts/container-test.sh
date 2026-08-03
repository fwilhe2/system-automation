#!/bin/bash

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

set -o nounset
set -o errexit

usage() {
    cat <<'EOF'
Usage: ./scripts/container-test.sh [DISTRO[:VERSION]] [ENTRYPOINT]

Builds the test image for DISTRO and runs the test suite in it. This is what
the CI workflow runs, so a green run here is the same run CI makes.

DISTRO defaults to fedora. VERSION defaults to the first value listed below:

  debian      testing, stable, unstable
  ubuntu      latest, rolling, devel
  fedora      latest, rawhide
  el          almalinux:10
  opensuse    tumbleweed, leap:16.0
  archlinux   latest

ENTRYPOINT replaces the test runner, e.g. bash for an interactive shell.

Examples:
  ./scripts/container-test.sh                   # fedora:latest, full test suite
  ./scripts/container-test.sh debian:unstable
  ./scripts/container-test.sh fedora:rawhide bash
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

cd "$(dirname "$0")/.."

SPEC=${1:-fedora}
DISTRO=${SPEC%%:*}
VERSION=''
if [[ "$SPEC" == *:* ]]; then
    VERSION=${SPEC#*:}
fi

# Every Containerfile takes the same build argument: the image to build on.
case "$DISTRO" in
    debian) CONTAINERFILE=dpkg IMAGE="debian:${VERSION:-testing}" ;;
    ubuntu) CONTAINERFILE=dpkg IMAGE="ubuntu:${VERSION:-latest}" ;;
    fedora) CONTAINERFILE=fedora IMAGE="fedora:${VERSION:-latest}" ;;
    el) CONTAINERFILE=el IMAGE="${VERSION:-almalinux:10}" ;;
    opensuse) CONTAINERFILE=opensuse IMAGE="registry.opensuse.org/opensuse/${VERSION:-tumbleweed}" ;;
    archlinux) CONTAINERFILE=archlinux IMAGE="archlinux:${VERSION:-latest}" ;;
    *)
        echo "Unknown distro: $DISTRO" >&2
        usage >&2
        exit 1
        ;;
esac

# Image tags may not contain a colon or a slash, which the el and opensuse
# image references do.
TAG="system-automation-$DISTRO${VERSION:+-${VERSION//[^a-zA-Z0-9_.-]/-}}"

# podman when it is there, docker otherwise. CONTAINER_CLI overrides that, which
# is what CI uses: its runners have both installed and the jobs are meant to run
# on docker.
CLI=${CONTAINER_CLI:-docker}
[[ -z "${CONTAINER_CLI:-}" ]] && command -v podman >/dev/null 2>&1 && CLI=podman

# None of the images run systemd as pid 1. Under docker, ansible's systemd
# module notices that on its own and skips the unit handling with a warning.
# Under podman it does not -- is_chroot() compares / against /proc/1/root,
# which match there -- so it runs systemctl for real and the docker role fails
# with "Service is in unknown state". SYSTEMD_OFFLINE puts both runtimes on the
# path docker takes by itself.
#
# Do not add --privileged. The fedora and el images build pam and sudo against
# libaudit, and in a privileged container the audit netlink socket reaches the
# host kernel, where PAM's account lookup fails: every privileged task dies with
# "Premature end of stream waiting for become success" and either "su:
# Authentication failure" or "PAM account management error". The dpkg images are
# unaffected because Debian does not link pam_unix against libaudit. It only
# shows on GitHub's runners, never on a local docker or podman host with no
# audit daemon running, so a green local run does not clear this one.
RUN_ARGS=(--rm --tty --env SYSTEMD_OFFLINE=1)

# Interactive only when there is a terminal to attach to, so this also works
# as a CI step
[[ -t 0 ]] && RUN_ARGS+=(--interactive)

# The virtualization role reads it to lift the anonymous GitHub API rate limit
[[ -n "${GITHUB_TOKEN:-}" ]] && RUN_ARGS+=(--env GITHUB_TOKEN)

if [[ "$#" -ge 2 ]]; then
    RUN_ARGS+=("--entrypoint=$2")
fi

set -x
$CLI build --build-arg="VERSION=$IMAGE" -t "$TAG" --file "test/container/Containerfile.$CONTAINERFILE" .
$CLI run "${RUN_ARGS[@]}" "$TAG"
