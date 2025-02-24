#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Run 'pip install pihole6api' to install it.")

DOCUMENTATION = r'''
---
module: dhcp_remove_lease
short_description: Remove DHCP leases via Pi-hole v6 API.
description:
    - This module removes DHCP leases from a Pi-hole v6 instance using the pihole6api Python client.
    - Leases can be removed by filtering on `ip`, `name`, `clientid`, or `hwaddr`.
    - If multiple filters are specified, only leases that match all criteria will be removed.
options:
    ip:
        description:
            - The IP address of the DHCP lease to remove.
        required: false
        type: str
    name:
        description:
            - The hostname of the DHCP lease to remove.
        required: false
        type: str
    clientid:
        description:
            - The Client ID (DHCP Unique Identifier) of the lease to remove.
        required: false
        type: str
    hwaddr:
        description:
            - The hardware (MAC) address of the lease to remove.
        required: false
        type: str
    password:
        description:
            - The API password for the Pi-hole instance.
        required: true
        type: str
        no_log: true
    url:
        description:
            - The URL of the Pi-hole instance.
        required: true
        type: str
author:
    - Shane Barbetta (@sbarbett)
'''

EXAMPLES = r'''
- name: Remove DHCP lease by IP
  sbarbett.pihole.dhcp_remove_lease:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    ip: "10.0.7.50"

- name: Remove DHCP lease by hostname
  sbarbett.pihole.dhcp_remove_lease:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    name: "test-host1"

- name: Remove all leases with specific MAC address
  sbarbett.pihole.dhcp_remove_lease:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    hwaddr: "aa:bb:cc:dd:ee:f1"

- name: Remove leases that match multiple parameters
  sbarbett.pihole.dhcp_remove_lease:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    name: "test-host2"
    clientid: "01:aa:bb:cc:dd:ee:f2"
'''

RETURN = r'''
result:
    description: The API response from the Pi-hole server.
    type: dict
    returned: always
changed:
    description: Whether any change was made.
    type: bool
    returned: always
'''

def run_module():
    module_args = dict(
        ip=dict(type='str', required=False),
        name=dict(type='str', required=False),
        clientid=dict(type='str', required=False),
        hwaddr=dict(type='str', required=False),
        password=dict(type='str', required=True, no_log=True),
        url=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        result={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    ip = module.params['ip']
    name = module.params['name']
    clientid = module.params['clientid']
    hwaddr = module.params['hwaddr']
    password = module.params['password']
    url = module.params['url']

    filters = {k: v for k, v in {'ip': ip, 'name': name, 'clientid': clientid, 'hwaddr': hwaddr}.items() if v}

    if not filters:
        module.fail_json(msg="At least one of 'ip', 'name', 'clientid', or 'hwaddr' must be specified.")

    if module.check_mode:
        module.exit_json(**result)

    try:
        client = PiHole6Client(url, password)

        # Retrieve existing DHCP leases
        leases = client.dhcp.get_leases().get("leases", [])

        # Find leases that match ALL specified filters
        matching_leases = [
            lease for lease in leases
            if all(lease.get(key) == value for key, value in filters.items())
        ]

        if not matching_leases:
            result['changed'] = False
            result['result'] = {"msg": "No matching leases found"}
            module.exit_json(**result)

        # Remove each matching lease
        responses = []
        for lease in matching_leases:
            response = client.dhcp.remove_lease(lease["ip"])
            responses.append({"ip": lease["ip"], "response": response})

        result['changed'] = True
        result['result'] = responses

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error removing DHCP lease: {e}", **result)
    finally:
        if client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main()
