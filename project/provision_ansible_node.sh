#!/bin/bash

apt-get -y install ansible
script="/etc/ansible/inventory.py"

cp inventory.py $script
cp hosts.yaml /etc/ansible/hosts.yaml
chmod 755 $script
sed -i '/^hostfile/d' /etc/ansible/ansible.cfg
sed -i "/\[defaults\]/a hostfile = $script" /etc/ansible/ansible.cfg
