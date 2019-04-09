#!/usr/bin/env python
import argparse
import json
import yaml
import sys


def read_inventory():
    f = open('/etc/ansible/hosts.yaml', 'r')
    raw_data = f.read()
    yaml_data = yaml.load(raw_data)
    json_data = json.dumps(yaml_data, indent=4, sort_keys=True)
    return json_data


def output_list_inventory(json_output):
    '''
    Output the --list data structure as JSON
    '''
    print json_output
    #print json.dumps(json_output)


def find_host(host, json_data):
    '''
    Find the given variables for the given host and output them as JSON
    '''
    inventory = json.loads(json_data)
    hostvars = inventory['_meta']['hostvars']
    host_attribs = json.dumps(hostvars.get(host), {}, sort_keys=True, indent=4)
    #host_attribs = json.dumps(inventory.get(host, {}))
    #host_attribs = inventory.get(search_host, {})
    print host_attribs


def main():
    '''
    Ansible dynamic inventory experimentation
    Output dynamic inventory as JSON from statically defined data structures
    '''

    # Argument parsing
    parser = argparse.ArgumentParser(description="Ansible dynamic inventory")
    parser.add_argument("--list", help="Ansible inventory of all of the groups",
                        action="store_true", dest="list_inventory")
    parser.add_argument("--host", help="Ansible inventory of a particular host", action="store",
                        dest="ansible_host", type=str)

    cli_args = parser.parse_args()
    list_inventory = cli_args.list_inventory
    ansible_host = cli_args.ansible_host
    json_data = read_inventory()

    if list_inventory:
        #output_list_inventory(ANSIBLE_INV)
        output_list_inventory(json_data)

    if ansible_host:
        find_host(ansible_host, json_data)


if __name__ == "__main__":
    main()
