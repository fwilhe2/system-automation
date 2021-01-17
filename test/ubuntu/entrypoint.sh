#!/bin/bash -l

ansible-playbook -vv /mnt/common.yml

source ~/.custom-path.sh

java -version
mvn --version