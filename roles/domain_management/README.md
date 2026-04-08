# domain_management

This role manages Pi-hole domains (allow/deny lists) across multiple Pi-hole instances. It processes domains using batch processing for efficiency, supporting both exact and regex domain types.

## Overview

- Manage domains on multiple Pi-hole instances using batch processing
- Ensure idempotent operations: domains are created, updated, or removed based on the desired state
- Support for exact and regex domain matching
- Associate domains with groups using human-readable group names
- Handle multiple domains per entry (e.g., lists of domains)

## Requirements

- **Ansible:** 2.9 or later
- **Python:** The control node must have the `pihole6api` library installed
- **Pi-hole API Access:** Each Pi-hole instance must be accessible with a valid URL and API password

## Role Variables

### `pihole_hosts`

A list of dictionaries representing the Pi-hole instances you want to manage. Each dictionary should include:

- `name`: The URL of the Pi-hole instance (e.g., `https://pi.hole`)
- `password`: The API password for the instance

### `pihole_domains`

A list of domain definitions. Each domain is a dictionary with the following keys:

* `domain`: The domain name (string) or list of domain names (array of strings)
* `domain_type`: The type of domain. Allowed values are `allow` or `deny`
* `kind`: The kind of domain. Allowed values are `exact` or `regex`
* `comment`: (Optional) A comment describing the domain
* `groups`: (Optional) A list of group names to associate with the domain
* `enabled`: (Optional) Whether the domain is enabled. Default is `true`
* `state`: Desired state for the domain. Allowed values are `present` or `absent`

## Example Playbook

```yaml
---
- name: Manage Pi-hole domains
  hosts: localhost
  gather_facts: false
  roles:
    - role: sbarbett.pihole.domain_management
      vars:
        pihole_hosts:
          - name: "https://your-pihole-1.example.com"
            password: "{{ pihole_password }}"
          - name: "https://your-pihole-2.example.com"
            password: "{{ pihole_password }}"
        
        pihole_domains:
          - domain: example.com
            domain_type: deny
            kind: exact
            comment: Block example.com
            groups:
              - Default
            enabled: true
            state: present
          - domain: "(\\.|^)googlevideo\\.com$"
            domain_type: deny
            kind: regex
            comment: Google Video
            groups: 
              - Echos
            enabled: false
            state: present
          - domain: 
              - msh.amazon.com
              - msh.amazon.co.uk
              - arcus-uswest.amazon.com
            domain_type: deny
            kind: exact
            groups: 
              - Echos
            enabled: True
            state: present
          - domain: old.example.com
            domain_type: allow
            kind: exact
            state: absent
```
