# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT

ARG VERSION

FROM $VERSION

ENV TERM=xterm

# The images carry a root account with a throwaway password and no sudo rules,
# so the test inventory escalates with su
ENV ANSIBLE_BECOME_METHOD=su

RUN dnf --assumeyes update && dnf --assumeyes --allowerasing install ansible-core python3 python3-pip python3-distro git unzip bash coreutils curl \
  && mkdir -p /home/user && echo "user:x:1001:1001:user:/home/user:/bin/bash" >> /etc/passwd \
  && chown -R user /home/user

RUN echo 'root:toor123' | chpasswd

USER user

COPY . /home/user

# ansible.cfg is only read from the working directory, so the repo copy is
# picked up here rather than the image running without any config at all
WORKDIR /home/user

ENTRYPOINT ["python3", "/home/user/test/container/run-test.py"]
