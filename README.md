# pihole-ansible

This collection provides Ansible modules and roles for managing PiHole v6 via a custom API client. This collection is built on top of the [piholev6api](https://github.com/sbarbett/piholev6api) Python library, which handles authentication and requests.

## Overview

This collection includes:

- **Modules:**
  - `local_a_record`: Manage local A records.
  - `local_cname`: Manage local CNAME records.

- **Roles:**
  - `manage_local_records`: A role that iterates over one or more PiHole hosts and manages a batch of local DNS records (both A and CNAME) as defined by the user. For more details, please see the [role's README](roles/manage_local_records/README.md).

In future releases, additional roles and modules will be added to further extend the capabilities of this collection.

## Getting Started

### Prerequisites

- **Ansible:** Version 2.9 or later.
- **Python:** The control node requires Python 3.x.
- **piholev6api Library:**  
  Install the piholev6api library using pip:
  
  ```bash
  pip install piholev6api
  ```

### Installation

Install the collection via Ansible Galaxy:

```bash
ansible-galaxy collection install sbarbett.pihole
```

You can also build it locally:

```bash
git clone https://github.com/sbarbett/pihole-ansible
ansible-galaxy collection build
ansible-galaxy collection install sbarbett-pihole-x.x.x.tar.gz
```

## Usage Examples

### Create an A Record

```yaml
---
- name: Create test.example.com A record
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Create test.example.com A record
      sbarbett.pihole.local_a_record:
        host: test.example.com
        ip: 127.0.0.2
        state: present
        url: "{{ test_pihole_2 }}"
        password: "{{ pihole_password }}"
```

### Delete an A Record

```yaml
---
- name: Delete test.example.com A record
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Delete test.example.com A record
      sbarbett.pihole.local_a_record:
        host: test.example.com
        ip: 127.0.0.1
        state: absent
        url: "{{ test_pihole_2 }}"
        password: "{{ pihole_password }}"
```

### Create a CNAME

```yaml
---
- name: Create canonical.example.com CNAME
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Create canonical.example.com CNAME
      sbarbett.pihole.local_cname:
        host: canonical.example.com
        target: test.example.com
        ttl: 901
        state: present
        url: "{{ test_pihole_2 }}"
        password: "{{ pihole_password }}"
```

### Delete a CNAME

```yaml
---
- name: Delete canonical.example.com CNAME
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Delete canonical.example.com CNAME
      sbarbett.pihole.local_cname:
        host: canonical.example.com
        target: test.example.com
        state: absent
        url: "{{ test_pihole_2 }}"
        password: "{{ pihole_password }}"
```

### Multiple Records & Instances

Using the provided role you can manage multiple records on many instances in one play.

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

## Documentation

* Each module includes embedded documentation. You can review the options by using `ansible-doc sbarbett.pihole.local_a_record` or `ansible-doc sbarbett.pihole.local_cname`.
* Detailed information for the `manage_local_records` role is provided in its own `README` file within the role directory.

## License

MIT