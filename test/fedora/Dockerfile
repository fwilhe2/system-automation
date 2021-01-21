FROM fedora:33

ENV TERM=xterm

RUN dnf --assumeyes update && dnf --assumeyes install git ansible curl unzip bash

# Install Ansible inventory file.
# Taken from https://github.com/geerlingguy/docker-ubuntu1804-ansible/blob/97a8d76f87dc4a15e24c88214806448246fbfb98/Dockerfile#L37
RUN mkdir -p /etc/ansible
RUN echo "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]