#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Run 'pip install pihole6api' to install it.")

DOCUMENTATION = r'''
---
module: pihole_local_cname
short_description: Manage Pi-hole local CNAME records via the pihole v6 API.
description:
    - This module adds or removes local CNAME records on a Pi-hole instance using the piholev6api Python client.
options:
    host:
        description:
            - The CNAME alias (record name) to manage.
        required: true
        type: str
    target:
        description:
            - The target host for the CNAME record.
        required: true
        type: str
    ttl:
        description:
            - The TTL (time-to-live) value for the record.
        required: false
        type: int
        default: 300
    state:
        description:
            - Whether the CNAME record should be present or absent.
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
    - Your Name (@yourhandle)
'''

EXAMPLES = r'''
- name: Create test2.example.com CNAME record
  sbarbett.pihole.local_cname:
    host: test2.example.com
    target: test.example.com
    ttl: 300
    state: present
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

- name: Remove test2.example.com CNAME record
  sbarbett.pihole.local_cname:
    host: test2.example.com
    target: test.example.com
    ttl: 300
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
        target=dict(type='str', required=True),
        ttl=dict(type='int', required=False, default=300),
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
    target = module.params['target']
    ttl = module.params['ttl']
    state = module.params['state']
    password = module.params['password']
    url = module.params['url']

    if module.check_mode:
        module.exit_json(**result)

    try:
        client = PiHole6Client(url, password)
        current_config = client.config.get_config_section("dns/cnameRecords")
        cname_list = current_config.get("config", {}).get("dns", {}).get("cnameRecords", [])

        existing_target = None
        existing_ttl = None
        for entry in cname_list:
            # Each entry is expected to be "host,target,ttl"
            parts = entry.split(',')
            if len(parts) == 3:
                rec_host, rec_target, rec_ttl = parts
                try:
                    rec_ttl = int(rec_ttl)
                except ValueError:
                    rec_ttl = rec_ttl
                if rec_host == host:
                    existing_target = rec_target
                    existing_ttl = rec_ttl
                    break

        if state == 'present':
            if existing_target is None:
                # No record exists; add the new CNAME record.
                add_response = client.config.add_local_cname(host, target, ttl=ttl)
                result['changed'] = True
                result['result'] = add_response
            elif existing_target != target or existing_ttl != ttl:
                # Record exists but with different target or ttl; remove then re-add.
                remove_response = client.config.remove_local_cname(host, existing_target, ttl=existing_ttl)
                add_response = client.config.add_local_cname(host, target, ttl=ttl)
                result['changed'] = True
                result['result'] = {'removed': remove_response, 'added': add_response}
            else:
                result['changed'] = False
                result['result'] = {"msg": "CNAME record already exists with the desired target and ttl", "current": current_config}

        elif state == 'absent':
            if existing_target is not None:
                remove_response = client.config.remove_local_cname(host, existing_target, ttl=existing_ttl)
                result['changed'] = True
                result['result'] = remove_response
            else:
                result['changed'] = False
                result['result'] = {"msg": "CNAME record does not exist", "current": current_config}

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error managing local CNAME record: {e}", **result)
    finally:
        if client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main()
