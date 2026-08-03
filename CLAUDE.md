# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Ansible playbooks that set up the author's Linux machines. `README.adoc` covers end-user
usage; this file covers working *on* the repo.

## Commands

`ansible.cfg` carries the inventory, the role paths and the collection path, so every
command below has to run from the repository root and needs no flags of its own.

```bash
ansible-playbook --ask-become-pass site.yml              # everything
ansible-playbook --ask-become-pass playbooks/common.yml  # just the headless half
./scripts/run.sh desktop                                 # same, playbook name without .yml

# Iterate on a single role: every role is tagged with its own name in the playbook
ansible-playbook --ask-become-pass playbooks/desktop.yml --tags firefox

ansible-playbook --syntax-check site.yml   # what CI's syntax-check job runs
./scripts/format-files.sh                  # prettier over **/*.yml, minus .prettierignore
reuse lint                                 # licence headers, enforced by its own workflow

# What the lint workflow runs. The repo is clean at ansible-lint's production
# profile; keep it that way. Configuration (exclusions, skipped rules and why)
# lives in .ansible-lint.
uvx --from ansible-lint ansible-lint
npx prettier --check "./**/*.yml"
shellcheck scripts/*.sh
```

### Container tests

`test/container/run-test.py` is the runner: it applies common and desktop, each twice, then
calls the assertions in `test/container/assertions.py`, which are what checks the resulting
system. A "single test" is one distro image.

```bash
# container-test.sh takes distro[:version] and maps it onto a Containerfile and the
# image its VERSION build argument names. The version defaults to the first one its
# --help lists for that distro. CI calls this same script, so a green run here is the
# run CI makes.
./scripts/container-test.sh                  # fedora:latest, full suite
./scripts/container-test.sh debian:unstable
./scripts/container-test.sh fedora bash      # ...with a shell instead of the test runner
```

The containers cannot use the inventory from `ansible.cfg`, which has no way to escalate
privileges. They pass `--inventory test/container/inventory.yml`, which carries the
throwaway root password, and each Containerfile sets the `ANSIBLE_BECOME_METHOD` that works
on that distribution - `su` everywhere except openSUSE and Arch, which get passwordless
sudo instead.

The run must not be `--privileged`. The fedora and el images build pam and sudo against
libaudit, and in a privileged container the audit netlink socket reaches the host kernel,
where PAM's account lookup fails and every privileged task dies at the first `become`. This
only shows on GitHub's runners, never on a local host with no audit daemon running, so a
green local run does not clear it.

Under podman the run needs `--env SYSTEMD_OFFLINE=1` or the docker role fails on the
missing init system; `container-test.sh` always passes it, and it is a no-op under docker.
`.dockerignore` keeps local scratch directories (`.ansible` above all) out of the build
context, where `COPY . /home/user` would land them root-owned and break every playbook run.

Inside an interactive container, `python3 test/container/run-playbook.py <name>` applies one
playbook without the assertions.

Lima VMs are the higher-fidelity option; see the Testing section of `README.adoc`.

## Architecture

**Playbooks compose roles; roles hold all logic.** `site.yml` imports
`playbooks/common.yml` (headless) and `playbooks/desktop.yml`; both are role lists with no
tasks of their own. Do not add a `tasks:` section to a playbook - make it a role.

Every role is tagged with its own name where the playbook lists it, which covers all of its
tasks. Tags do not belong on individual tasks; `notest` (below) is the exception and it also
goes on the role.

**Configuration is role defaults plus one shared file.** Each role's inputs, package lists
above all, live in `roles/<role>/defaults/main.yml`. Variables used by more than one role
live in `playbooks/group_vars/all/defaults.yml`, which currently means `username` alone.

Overrides go in the gitignored `playbooks/group_vars/all/local.yml`: everything in
`group_vars/all/` is loaded and merged, and group vars outrank role defaults, so only the
keys that file names are overridden. This is plain variable precedence - it needs no
`vars_files`, no `include_vars` pre-task and no `tags: always`, and none of those should be
reintroduced.

Role variables are prefixed with the role name (`directories_paths`, `vscodium_extensions`),
which ansible-lint's production profile enforces.

**Everything must work on five package managers and two architectures.** Debian/Ubuntu,
Fedora, EL, openSUSE and Arch, on amd64 and arm64. The three mechanisms for this:

- Package lists are dicts keyed by `ansible_facts['os_family']`, installed as one list in
  one transaction: `name: "{{ basic_packages[ansible_facts['os_family']] }}"`. Do not loop
  the package module per item, and do not add `ignore_errors` - a name that does not exist
  on a distribution is a bug in that distribution's list, and CI covers every one of them.
  Where the family is not fine-grained enough, key by `ansible_facts['distribution']` with
  the family as the `default()` (see `roles/virtualization/defaults/main.yml`).
- Where a whole role cannot work somewhere, the `when:` guard lives on the role in the
  playbook (see the vscode entry in `playbooks/desktop.yml`), with a comment saying why.
- Distro-specific task files (`roles/docker/tasks/deb.yml`) are imported from the role's
  `main.yml` when the split is too large for a `when:`.

`become: true` goes on the role in the playbook when every task in it needs root. Only roles
that mix privileged and unprivileged tasks (`firefox`, `virtualization`) set it per task.

**Idempotence is a hard contract.** `run_ansible()` in `run-test.py` applies every playbook
twice and fails unless the second run reports `changed=0`. A task that always reports changed
turns every container job red. In practice: `ansible.builtin.command` needs `changed_when`,
and anything else should be expressed as state rather than as a command - see how the
virtualization role compares `limactl --version` against the latest release tag and skips
the download entirely instead of masking it with `changed_when: false`. The firefox role
does use `changed_when: false` on its download and extraction, because the nightly build
behind the URL can change between the two runs.

Tag a role `notest` to have CI skip it (`--skip-tags notest`); currently only flatpak uses it.

**Vendored roles** live in `vendor/roles/` and are on the role path via `ansible.cfg`.
`greenleader.codium`, `iesplin.vscode`, `gotmax23.epel*` and `bodsch.ansible-snapd` are
third-party copies whose licences `README.adoc` documents, as is
`roles/vscodium/library/codium_extensions.py`. Prefer working around them over editing them;
`vendor/` is excluded from both `.ansible-lint` and `.prettierignore` so the linters do not
push edits into them.

## Conventions

- Every file needs SPDX headers (`# SPDX-FileCopyrightText: Florian Wilhelm` /
  `# SPDX-License-Identifier: MIT`), enforced by the REUSE workflow. For formats without
  comments, put the tags in a Jinja comment in the `.j2` template or add a `.license`
  sidecar next to the file (see `CLAUDE.md.license`).
- YAML is prettier-formatted. `.j2` templates are not.
- Facts are referenced as `ansible_facts['os_family']`, never as top-level `ansible_*`
  variables, which ansible-core 2.24 removes. Single quotes inside the brackets: the
  double-quoted form nests badly inside double-quoted YAML scalars. `ansible_version` and
  `ansible_managed` are magic variables rather than facts and keep their names.
