# 🍓 pihole-ansible

This collection provides Ansible modules and roles for managing PiHole v6 via a custom API client. This collection is built on top of the [pihole6api](https://github.com/sbarbett/pihole6api) Python library, which handles authentication and requests.

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
- **pihole6api Library**

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

#### `pihole6api` Dependency

The `pihole6api` library is required for this Ansible collection to function. The installation method depends on how you installed Ansible.

```bash
pip install pihole6api
```

However, some Linux distributions (Debian, Ubuntu, Fedora, etc.) **restrict system-wide `pip` installs** due to [PEP 668](https://peps.python.org/pep-0668/). In that case, use one of the methods below.

**Installing in a Virtual Environment (Recommended):**

If you want an isolated environment that won’t interfere with system-wide packages, install both `pihole6api` and Ansible in a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install pihole6api ansible
```

To confirm that `ansible` and `pihole6api` are installed correctly within the environment, run:

```bash
which python && which ansible
python -c "import pihole6api; print(pihole6api.__file__)"
```

To exit the virtual environment:

```bash
deactivate
```

**Using `pipx`:**

If Ansible is installed via `pipx`, inject `pihole6api` into Ansible’s environment:

```bash
pipx inject ansible pihole6api --include-deps
```

Verify installation:

```bash
pipx runpip ansible show pihole6api
```

Since Ansible does not automatically detect `pipx` environments, you must explicitly set the Python interpreter in your Ansible configuration:

Edit `ansible.cfg`:

```
[defaults]
interpreter_python = ~/.local/pipx/venvs/ansible/bin/python
```

For more information on `pipx` see [the official documentation](https://github.com/pypa/pipx) and [the Ansible install guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html).

**Installing for System-Wide Ansible (Generally Not Recommended):**

If Ansible was installed via a package manager (`apt`, `dnf`, `brew`) and a virtual environment or `pipx` is not a feasible or desired solution, run `pip` with `--break-system-packages` to bypass **PEP 668** restrictions:

```bash
sudo pip install --break-system-packages pihole6api
```

Verify installation:

```bash
python3 -c "import pihole6api; print(pihole6api.__file__)"

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
