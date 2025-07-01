# manage_local_records_lxc

This role is designed to manage local DNS records (both A and AAAA) from Anisble Proxmox Inventory plugin on one or more Pi-hole instances. It iterates over a list of Pi-hole hosts and applies all changes from the Proxmox invenotry facts.

## Overview

- Manage local A and AAAA records on multiple Pi-hole instances.
- use facts from [Proxmox inventory source](https://docs.ansible.com/ansible/latest/collections/community/general/proxmox_inventory.html)
- Almost idempotent operations: records are added, updated but not removed if a LXC is removed.

## Requirements

- **Ansible:** 2.9 or later.
- **Python:** The control node must have the `piholev6api` library installed.
- **Pi-hole API Access:** Each Pi-hole instance must be accessible with a valid URL and API password.
- **Proxmox Invenotry:** see example below

## Role Variables

### `pihole_hosts`

A list of dictionaries representing the Pi-hole instances you want to manage. Each dictionary should include:

- `name`: The URL of the Pi-hole instance (e.g., `https://pi.hole`).
- `password`: The API password for the instance.


## Example Inventory
```
### Proxmox
# https://docs.ansible.com/ansible/latest/collections/community/general/proxmox_inventory.html
plugin: community.general.proxmox
user: ansible@pve
token_id: inventory
token_secret: ae9b7531-ddca-...
url: https://100.64.64.1:8006

validate_certs: false
want_facts: true
facts_prefix: proxmox_
group_prefix: proxmox_
want_proxmox_nodes_ansible_host: true
compose:
  ansible_host: proxmox_ipconfig0.ip | default(proxmox_net0.ip) | ipaddr('address')
```


## Example Playbook

```yaml
---
- name: Manage DNS records for Proxmox LXC's
  hosts: all
  gather_facts: True
  connection: local
  roles:
    - role: sbarbett.pihole.manage_proxmox_lxc_records
      vars:
        pihole_hosts:
          - name: "https://test-pihole-1.example.xyz"
            password: "{{ pihole_password }}"
          - name: "https://test-pihole-2.example.xyz"
            password: "{{ pihole_password }}"
```

if running on all, you might apply a host/group filter

```
ap plays/proxmox-zone.yaml --limit mygroup
```


