# manage_local_records

This role is designed to manage local DNS records (both A and CNAME) on one or more Pi-hole instances. It iterates over a list of Pi-hole hosts and applies record changes as defined by the user.

## Overview

- Manage local A and CNAME records on multiple Pi-hole instances.
- Ensure idempotent operations: records are added, updated, or removed based on the desired state.

## Requirements

- **Ansible:** 2.9 or later.
- **Python:** The control node must have the `piholev6api` library installed.
- **Pi-hole API Access:** Each Pi-hole instance must be accessible with a valid URL and API password.

## Role Variables

### `pihole_hosts`

A list of dictionaries representing the Pi-hole instances you want to manage. Each dictionary should include:

- `name`: The URL of the Pi-hole instance (e.g., `https://pi.hole`).
- `password`: The API password for the instance.

### `pihole_records`

A list of record definitions. Each record is a dictionary with the following keys:

* `name`: The DNS record name.
* `type`: The record type. Allowed values are `A` or `CNAME`.
* `data`: For A records, this is the IP address; for CNAME records, this is the target hostname.
* `state`: Desired state for the record. Allowed values are `present` or `absent`.
* `ttl`: (Optional, for CNAME records) Time-to-live value (default is 300 seconds).

## Example Playbook

```yaml
---
- name: Manage Pi-hole local records
  hosts: localhost
  gather_facts: false
  roles:
    - role: sbarbett.pihole.manage_local_records
      vars:
        pihole_hosts:
          - name: "https://test-pihole-1.example.xyz"
            password: "{{ pihole_password }}"
          - name: "https://test-pihole-2.example.xyz"
            password: "{{ pihole_password }}"
        pihole_records:
          - name: dummy1.xyz
            type: A
            data: "192.168.1.1"
            state: present
          - name: dummy2.xyz
            type: CNAME
            data: dummy1.xyz
            state: present
          - name: dummy3.xyz
            type: A
            data: "127.0.0.1"
            state: present
          - name: dummy4.xyz
            type: CNAME
            data: dummy2.xyz
            ttl: 900
            state: present
```