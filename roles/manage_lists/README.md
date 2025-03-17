# manage_lists

This role is designed to manage allow lists and block lists on one or more Pi-hole instances. It iterates over a list of Pi-hole hosts and applies list changes as defined by the user.

## Overview

- Manage allow lists and block lists on multiple Pi-hole instances.
- Ensure idempotent operations: lists are added, updated, or removed based on the desired state.
- Validate that specified groups exist before attempting to apply them to lists.

## Requirements

- **Ansible:** 2.9 or later.
- **Python:** The control node must have the `piholev6api` library installed.
- **Pi-hole API Access:** Each Pi-hole instance must be accessible with a valid URL and API password.

## Role Variables

### `pihole_hosts`

A list of dictionaries representing the Pi-hole instances you want to manage. Each dictionary should include:

- `name`: The URL of the Pi-hole instance (e.g., `https://pi.hole`).
- `password`: The API password for the instance.

### `pihole_lists`

A list of list definitions. Each list is a dictionary with the following keys:

* `address`: The URL of the list.
* `type`: The list type. Allowed values are `allow` or `block`.
* `comment`: (Optional) A comment describing the list.
* `groups`: (Optional) A list of group IDs to associate with the list. The role will validate that these groups exist.
* `enabled`: (Optional) Whether the list is enabled. Default is `true`.
* `state`: Desired state for the list. Allowed values are `present` or `absent`.

## Example Playbook

```yaml
---
- name: Manage Pi-hole lists
  hosts: localhost
  gather_facts: false
  roles:
    - role: sbarbett.pihole.manage_lists
      vars:
        pihole_hosts:
          - name: "https://your-pihole-1.example.com"
            password: "{{ pihole_password }}"
          - name: "https://your-pihole-2.example.com"
            password: "{{ pihole_password }}"
        pihole_lists:
          - address: "https://example.com/whitelist.txt"
            type: "allow"
            comment: "Example whitelist"
            state: present
          - address: "https://example.com/blocklist.txt"
            type: "block"
            comment: "Example blocklist"
            state: present
          - address: "https://example.com/blocklist2.txt"
            type: "block"
            comment: "Example blocklist with groups"
            groups: [0, 1]
            state: present
          - address: "https://example.com/whitelist2.txt"
            type: "allow"
            comment: "Example whitelist with groups"
            groups: [0, 1]
            state: present
          - address: "https://example.com/old-blocklist.txt"
            type: "block"
            state: absent
```