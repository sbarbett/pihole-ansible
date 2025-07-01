#!/usr/bin/python
# -*- coding: utf-8 -*-
# this is litteraly a clone of local_a_record.py but for AAAA records. pi-hole does not disgguish between A and AAAA records in the API, so this is just a copy of the other module with AAAA in the name

from ansible.module_utils.basic import AnsibleModule
try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Run 'pip install pihole6api' to install it.")

DOCUMENTATION = r'''
---
module: local_aaaa_record
short_description: Manage Pi-hole local AAAA records via pihole v6 API.
description:
    - This module adds or removes local AAAA records on a Pi-hole instance using the piholev6api Python client.
options:
    host:
        description:
            - The hostname for the AAAA record.
        required: true
        type: str
    ip:
        description:
            - The IP address to associate with the hostname.
        required: true
        type: str
    state:
        description:
            - Whether the A record should be present or absent.
        required: true
        type: str
        choices: ['present', 'absent']
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
- name: Create test.example.com AAAAA record
  sbarbett.pihole.local_aaaa_record:
    host: test.example.com
    ip: 2001:db8::1
    state: present
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

- name: Delete test.example.com AAAA record
  sbarbett.pihole.local_aaaa_record:
    host: test.example.com
    ip: 2001:db8::1
    state: absent
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
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
        host=dict(type='str', required=True),
        ip=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], required=True),
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

    host = module.params['host']
    ip = module.params['ip']
    state = module.params['state']
    password = module.params['password']
    url = module.params['url']

    if module.check_mode:
        module.exit_json(**result)

    try:
        client = PiHole6Client(url, password)
        current_config = client.config.get_config_section("dns/hosts")
        hosts_list = current_config.get("config", {}).get("dns", {}).get("hosts", [])

        existing_ip = None
        for entry in hosts_list:
            parts = entry.split(None, 1)  # expected format: "ip host"
            if len(parts) == 2 and parts[1] == host:
                # Simply/stupidly check if parts[0] is IPv6
                if ':' in parts[0]:
                    existing_ip = parts[0]
                    break

        if state == 'present':
            if existing_ip is None:
                # No record exists; add the new one.
                add_response = client.config.add_local_a_record(host, ip)
                result['changed'] = True
                result['result'] = add_response
            elif existing_ip != ip:
                # A record exists but with a different IP; remove it first.
                remove_response = client.config.remove_local_a_record(host, existing_ip)
                add_response = client.config.add_local_a_record(host, ip)
                result['changed'] = True
                result['result'] = {'removed': remove_response, 'added': add_response}
            else:
                result['changed'] = False
                result['result'] = {"msg": "Record already exists with the desired IP", "current": current_config}

        elif state == 'absent':
            if existing_ip is not None:
                remove_response = client.config.remove_local_a_record(host, existing_ip)
                result['changed'] = True
                result['result'] = remove_response
            else:
                result['changed'] = False
                result['result'] = {"msg": "Record does not exist", "current": current_config}

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error managing local AAAA record: {e}", **result)
    finally:
        if client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main()
