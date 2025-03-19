# group_client_manager

This role manages Pi-hole groups and clients across multiple Pi-hole instances. It processes groups first (since clients may reference them) and then handles clients, using batch processing for efficiency.

## Overview

- Manage groups and clients on multiple Pi-hole instances using batch processing
- Ensure idempotent operations: groups and clients are created, updated, or removed based on the desired state
- Process groups before clients to ensure proper dependencies
- Support for human-readable group names in client configurations

## Requirements

- **Ansible:** 2.9 or later
- **Python:** The control node must have the `pihole6api` library installed
- **Pi-hole API Access:** Each Pi-hole instance must be accessible with a valid URL and API password

## Role Variables

### `pihole_hosts`

A list of dictionaries representing the Pi-hole instances you want to manage. Each dictionary should include:

- `name`: The URL of the Pi-hole instance (e.g., `https://pi.hole`)
- `password`: The API password for the instance

### `pihole_groups`

A list of group definitions. Each group is a dictionary with the following keys:

* `name`: The name of the group
* `comment`: (Optional) A comment describing the group
* `enabled`: (Optional) Whether the group is enabled. Default is `true`
* `state`: Desired state for the group. Allowed values are `present` or `absent`

### `pihole_clients`

A list of client definitions. Each client is a dictionary with the following keys:

* `name`: The client IP address or CIDR range
* `comment`: (Optional) A comment describing the client
* `groups`: (Optional) A list of group names to associate with the client
* `state`: Desired state for the client. Allowed values are `present` or `absent`

## Example Playbook

```yaml
---
- name: Manage Pi-hole groups and clients
  hosts: localhost
  gather_facts: false
  roles:
    - role: sbarbett.pihole.group_client_manager
      vars:
        pihole_hosts:
          - name: "https://your-pihole-1.example.com"
            password: "{{ pihole_password }}"
          - name: "https://your-pihole-2.example.com"
            password: "{{ pihole_password }}"
        
        pihole_groups:
          - name: Default
            comment: "Default group"
            enabled: true
            state: present
          - name: IOT
            comment: "Internet of Things devices"
            enabled: true
            state: present
          - name: Restricted
            comment: "Restricted access devices"
            enabled: false
            state: present
          - name: OldGroup
            state: absent
        
        pihole_clients:
          - name: 192.168.1.0/24
            comment: "Main network"
            groups:
              - Default
            state: present
          - name: 192.168.2.0/24
            comment: "IOT network"
            groups:
              - IOT
              - Restricted
            state: present
          - name: 192.168.3.0/24
            state: absent
```
