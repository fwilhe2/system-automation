# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Ansible playbooks that set up the author's Linux machines. `README.adoc` covers end-user
usage; this file covers working *on* the repo.

## Commands

```bash
# Apply a playbook to this machine
ansible-playbook --ask-become-pass --inventory inventory common.yml
./run.sh desktop                     # same thing, playbook name without .yml

# Iterate on a single role (see the tagging caveat under Architecture)
ansible-playbook --ask-become-pass --inventory inventory desktop.yml --tags firefox

# What CI's syntax-check job runs
for p in common desktop epel snap; do
  ansible-playbook --inventory inventory --syntax-check "$p.yml"; done

./format-files.sh                    # prettier over **/*.yml, minus .prettierignore
reuse lint                           # licence headers, enforced by its own workflow

# What the lint workflow runs. The repo is clean at ansible-lint's default
# profile; keep it that way. Configuration (exclusions, skipped rules and why)
# lives in .ansible-lint.
uvx --from ansible-lint ansible-lint
npx prettier --check "./**/*.yml"
```

### Container tests

`test/container/run-test.py` is the whole suite: it applies epel, snap, common and desktop,
then asserts properties of the resulting system. A "single test" is one distro image.

```bash
./local-test-env.sh fedora           # interactive fedora:devel container
./local-test-env.sh fedora bash      # ...with a shell instead of the test runner

# Other distros: the VERSION arg is not uniform across Containerfiles.
# dpkg and el take a full image ref, fedora takes only the tag, opensuse takes the
# openSUSE registry path, archlinux takes none.
docker build --build-arg=VERSION=debian:testing -t sa-deb --file test/container/Containerfile.dpkg .
docker run --user user --tty --volume $PWD:/mnt sa-deb
```

Inside an interactive container, `python3 test/container/run-playbook.py <name>` applies one
playbook without the assertions.

Lima VMs are the higher-fidelity option; see the Testing section of `README.adoc`.

## Architecture

**Playbooks compose roles; roles hold all logic.** `common.yml` (headless) and `desktop.yml`
are role lists. `epel.yml` and `snap.yml` are prerequisites applied before the others.
Tagging is inconsistent: most roles repeat `tags: <role>` on every task, while `firefox` is
tagged where the playbook includes it. Check which of the two a role uses before relying on
`--tags`.

**Configuration is one variable file.** `default.config.yml` holds `username` plus package
lists, loaded via `vars_files`. Every playbook then has a `Load Configuration Overrides`
pre-task that `include_vars` a gitignored `config.yml` through
`query('first_found', ['config.yml'], errors='ignore')`, so the file is optional and only the
keys it defines are overridden. `include_vars` outranks `vars_files` in precedence, and the
pre-task is tagged `always` so overrides survive a `--tags` run. Do not fold this back into
`vars_files: - [default.config.yml, config.yml]`: that form takes the first file that exists,
which is always the default, so `config.yml` would never be read.

**Everything must work on five package managers and two architectures.** Debian/Ubuntu,
Fedora, EL, openSUSE and Arch, on amd64 and arm64. The two mechanisms for this:

- Package lists are dicts keyed by `ansible_os_family`, looped over as
  `basic_packages[ansible_os_family]`, usually with `ignore_errors: true` because names
  drift between distros.
- Where a whole role cannot work somewhere, the `when:` guard lives on the role in the
  playbook (see the vscode entry in `desktop.yml`), with a comment saying why.

Distro-specific task files (`roles/docker/tasks/deb.yml`) are included from the role's
`main.yml` when the split is too large for a `when:`.

**Idempotence is a hard contract.** `run_ansible()` in `run-test.py` applies every playbook
twice and fails unless the second run reports `changed=0`. A task that always reports changed
turns every container job red. In practice: `ansible.builtin.command` needs `changed_when`,
downloads and extractions that run unconditionally are marked `changed_when: false`, and
anything else should be expressed as state rather than as a command.

Tag a task `notest` to have CI skip it (`--skip-tags notest`); currently only flatpak uses it.

**Vendored roles.** `greenleader.codium`, `iesplin.vscode`, `gotmax23.epel*`,
`bodsch.ansible-snapd` and `library/codium-extensions` are third-party copies whose licences
`README.adoc` documents. Prefer working around them over editing them; they are excluded
from both `.ansible-lint` and `.prettierignore` so the linters do not push edits into them.

## Conventions

- Every file needs SPDX headers (`# SPDX-FileCopyrightText: Florian Wilhelm` /
  `# SPDX-License-Identifier: MIT`), enforced by the REUSE workflow. For formats without
  comments, put the tags in a Jinja comment in the `.j2` template or add a `.license`
  sidecar; `.reuse/dep5` covers the exceptions.
- YAML is prettier-formatted. `.j2` templates are not.
- Facts are referenced as `ansible_facts['os_family']`, never as top-level `ansible_*`
  variables, which ansible-core 2.24 removes. Single quotes inside the brackets: the
  double-quoted form nests badly inside double-quoted YAML scalars. `ansible_version` and
  `ansible_managed` are magic variables rather than facts and keep their names.
