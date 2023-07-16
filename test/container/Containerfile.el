ARG VERSION

FROM $VERSION

ENV TERM=xterm

RUN dnf --assumeyes update && dnf --assumeyes --allowerasing install python3 python3-pip python3-distro git unzip bash coreutils curl \
  && mkdir -p /home/user && echo "user:x:1001:1001:user:/home/user:/bin/bash" >> /etc/passwd \
  && chown -R user /home/user

# Install Ansible inventory file.
# Taken from https://github.com/geerlingguy/docker-fedora33-ansible/blob/bd54ebebc836c10e76938a7d52e2386b7f16960e/Dockerfile#L35
RUN mkdir -p /etc/ansible
RUN echo -e '[local]\nlocalhost ansible_connection=local ansible_become_password=toor123' > /etc/ansible/hosts

RUN echo 'root:toor123' | chpasswd

RUN python3 -m pip install --upgrade pip

USER user

RUN python3 -m pip install --user ansible

COPY . /home/user

ENTRYPOINT ["python3", "/home/user/test/container/run-test.py"]
