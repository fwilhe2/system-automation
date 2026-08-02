<!--
SPDX-FileCopyrightText: Sion Fandrick
SPDX-License-Identifier: MIT
 -->

Role Name
=========

Install Codium a community-driven, freely-licensed binary distribution of Microsoft’s editor VSCode.

Requirements
------------

None.

Role Variables
--------------

None

Dependencies
------------

None

Example Playbook
----------------

    - hosts: workstations
      roles:
         - { role: greenleader.codium, become: yes }

License
-------

MIT
