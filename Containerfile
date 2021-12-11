FROM vagrantlibvirt/vagrant-libvirt:latest

ENV TERM=xterm
ENV DEBIAN_FRONTEND=noninteractive

ADD https://bootstrap.pypa.io/get-pip.py get-pip.py

RUN apt-get -y update && apt-get -y install software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y \
  curl \
  bash \
  python3.11 \
  python3.11-dev \
  python3.11-distutils \
  unzip \
  libasound2 \
  && mkdir -p /home/user \
  && echo "user:x:1001:1001:user:/home/user:/bin/bash" >> /etc/passwd \
  && echo "user:x:1001:" >> /etc/group \
  && chown -R user /home/user

RUN python3.11 get-pip.py

# Install Ansible inventory file.
# Taken from https://github.com/geerlingguy/docker-ubuntu1804-ansible/blob/97a8d76f87dc4a15e24c88214806448246fbfb98/Dockerfile#L37
RUN mkdir -p /etc/ansible
RUN echo "[local]\nlocalhost ansible_connection=local ansible_become_password=toor123" > /etc/ansible/hosts

RUN echo 'root:toor123' | chpasswd

USER user

RUN python3.11 /usr/bin/pip install --user ansible

COPY . /home/user

WORKDIR /home/user
