#!/usr/bin/env python
import struct
import socket

def cidr(prefix):
    return socket.inet_ntoa(struct.pack(">I", (0xffffffff << (32 - prefix)) & 0xffffffff))

def read_base_config(file):
    lines = []
    for line in open(file, 'r'):
        if line.rstrip():
            lines.append(line.rstrip())
    return lines

def read_config_file(file):
    # load lines into content as a list
    contents = []
    lines = []
    for line in open(file):
        li = line.rstrip()
        if not li.startswith("#"):
            contents.append(line.rstrip())


    # TODO: convert it to a data structure that can be converted to yaml
    # right now it is pretty dumb
    count = 0
    lines.append('instances:')
    for row in contents:
        count += 1
        vpn_server_ip, proto, port, subnet, snat = row.split()
        subnet_prefix, mask_bit = subnet.split('/')
        subnet_mask = cidr(int(mask_bit))
        lines.append('  - name: instance%s'% count)
        lines.append('    vpn_server_ip: %s'% vpn_server_ip)
        lines.append('    subnet: %s'% subnet_prefix)
        lines.append('    subnet_mask: %s'% subnet_mask)
        lines.append('    subnet_mask_bit: %s'% mask_bit)
        lines.append('    proto: %s'% proto)
        lines.append('    port: %s'% port)
    return lines

def main():
    base_file = 'base/groupvars_all.template'
    config_file = 'config.file'
    output = 'ansible/group_vars/all'

    base_file_content = read_base_config(base_file)
    instances_config = read_config_file(config_file)
    
    f = open(output, 'w')
    for line in base_file_content:
        f.write(line+'\n')
    for line in instances_config:
        f.write(line+'\n')
    f.close()

main()
