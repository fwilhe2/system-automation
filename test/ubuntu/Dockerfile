FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
  ansible \
  curl \
  bash \
  unzip

# Install Ansible inventory file.
# Taken from https://github.com/geerlingguy/docker-ubuntu1804-ansible/blob/97a8d76f87dc4a15e24c88214806448246fbfb98/Dockerfile#L37
RUN mkdir -p /etc/ansible
RUN echo "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts
