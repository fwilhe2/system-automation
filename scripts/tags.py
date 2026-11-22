#!/usr/bin/env python3

# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

"""Lists the playbooks' role tags, and checks that they are documented.

    scripts/tags.py roles [PLAYBOOK...]  first tag of every role, in run order,
                                         as "<playbook> <tag>" lines
    scripts/tags.py check                fail unless the tags follow the
                                         convention and README.adoc's table
                                         lists exactly the tags in use

The playbooks are prettier-formatted, so a line-based parse is enough and keeps
this free of dependencies: it runs before anything is installed.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYBOOKS = ["playbooks/common.yml", "playbooks/desktop.yml"]
README = ROOT / "README.adoc"

ROLE = re.compile(r"^\s+- role: (\S+)\s*$")
TAGS = re.compile(r"^(\s+)tags: \[([^\]]*)\]\s*$")
TABLE_ROW = re.compile(r"^\| `([^`]+)`")


def parse(playbook):
    """Return (play_tags, [(role, [tags])]) for one playbook."""
    play_tags, roles, current = [], [], None
    for line in (ROOT / playbook).read_text().splitlines():
        if m := ROLE.match(line):
            current = (m.group(1), [])
            roles.append(current)
        elif m := TAGS.match(line):
            tags = [t.strip() for t in m.group(2).split(",") if t.strip()]
            if len(m.group(1)) == 2:  # on the play itself
                play_tags.extend(tags)
            elif current is not None:
                current[1].extend(tags)
    return play_tags, roles


def documented_tags():
    text = README.read_text()
    try:
        table = text.split("// tags-table-start", 1)[1].split("// tags-table-end", 1)[0]
    except IndexError:
        sys.exit("README.adoc: tags-table-start/-end markers not found")
    return {m.group(1) for line in table.splitlines() if (m := TABLE_ROW.match(line))}


def check():
    errors, used, referenced = [], set(), set()
    for playbook in PLAYBOOKS:
        play_tags, roles = parse(playbook)
        # A tag on the play also lands on its implicit fact gathering, which
        # then no longer runs under `--tags <role>`
        if play_tags:
            errors.append(f"{playbook}: tag the roles, not the play")
        expected = len(re.findall(r"^\s+- role: ", (ROOT / playbook).read_text(), re.M))
        if expected != len(roles):
            errors.append(f"{playbook}: parsed {len(roles)} of {expected} roles")
        for role, tags in roles:
            referenced.add(role)
            used.update(tags)
            if not tags:
                errors.append(f"{playbook}: role {role} has no tags")
            # Our own roles must lead with their own name; the vendored ones
            # are named by their tag (iesplin.vscode -> vscode)
            elif (ROOT / "roles" / role).is_dir() and tags[0] != role:
                errors.append(f"{playbook}: role {role}: first tag must be {role!r}, is {tags[0]!r}")

    for role_dir in sorted((ROOT / "roles").iterdir()):
        if role_dir.is_dir() and role_dir.name not in referenced:
            errors.append(f"roles/{role_dir.name} is not listed in any playbook")

    documented = documented_tags()
    for tag in sorted(used - documented):
        errors.append(f"README.adoc: tag {tag!r} is missing from the tags table")
    for tag in sorted(documented - used):
        errors.append(f"README.adoc: tag {tag!r} is in the tags table but used nowhere")

    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


def list_roles(playbooks):
    seen = set()
    for playbook in playbooks or PLAYBOOKS:
        for _role, tags in parse(playbook)[1]:
            if tags and (playbook, tags[0]) not in seen:
                seen.add((playbook, tags[0]))
                print(playbook, tags[0])
    return 0


if __name__ == "__main__":
    match sys.argv[1:2]:
        case ["check"]:
            sys.exit(check())
        case ["roles"]:
            sys.exit(list_roles(sys.argv[2:]))
        case _:
            sys.exit(__doc__)
