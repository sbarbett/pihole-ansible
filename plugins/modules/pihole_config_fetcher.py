#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Run 'pip install pihole6api' to install it.")

DOCUMENTATION = r'''
---
module: pihole_config_fetcher
short_description: Fetch Pi-hole DNS configuration once for batch processing
description:
    - This module fetches both hosts and CNAME records configuration from Pi-hole in a single call.
    - This is an implementation detail of the C(manage_local_records) role, which uses it to read
      the live configuration once per instance and then apply only the records that differ.
    - It is not part of the collection's supported interface. Its return shape may change without
      a deprecation cycle, so playbooks should not depend on it. Use the C(manage_local_records)
      role, or the C(local_a_record), C(local_aaaa_record) and C(local_cname) modules instead.
options:
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
requirements:
    - pihole6api
author:
    - Jason Learst (@jasonlearst)
'''

EXAMPLES = r'''
# Internal to the manage_local_records role; shown here only to document how the
# role consumes it. Use the role rather than calling this module directly.
- name: Fetch current Pi-hole DNS configuration
  sbarbett.pihole.pihole_config_fetcher:
    url: "{{ pihole_instance.name }}"
    password: "{{ pihole_instance.password }}"
  register: manage_local_records_config
  no_log: true
'''

RETURN = r'''
hosts_config:
    description: "Current A/AAAA hosts configuration as {hostname: {record_type: ip}}"
    type: dict
    returned: always
cnames_config:
    description: "Current CNAME records configuration as {hostname: {target: str, ttl: int|null}}"
    type: dict
    returned: always
'''

def run_module():
    module_args = dict(
        password=dict(type='str', required=True, no_log=True),
        url=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        hosts_config={},
        cnames_config={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    password = module.params['password']
    url = module.params['url']

    try:
        client = PiHole6Client(url, password)

        # Fetch hosts configuration
        hosts_config = client.config.get_config_section("dns/hosts")
        hosts_list = hosts_config.get("config", {}).get("dns", {}).get("hosts", [])

        # Parse hosts into nested dictionary {hostname: {record_type: ip}}
        # This correctly handles hostnames with both A and AAAA records
        hosts_dict = {}
        for entry in hosts_list:
            parts = entry.split(None, 1)
            if len(parts) == 2:
                ip, hostname = parts
                record_type = "AAAA" if ':' in ip else "A"
                if hostname not in hosts_dict:
                    hosts_dict[hostname] = {}
                hosts_dict[hostname][record_type] = ip

        # Fetch CNAME configuration
        cnames_config = client.config.get_config_section("dns/cnameRecords")
        cnames_list = cnames_config.get("config", {}).get("dns", {}).get("cnameRecords", [])

        # Parse CNAMEs into dictionary {hostname: {target: str, ttl: int|None}}
        cnames_dict = {}
        for entry in cnames_list:
            parts = entry.split(',')
            if len(parts) >= 2:
                hostname = parts[0]
                target = parts[1]
                ttl = None
                if len(parts) == 3:
                    try:
                        ttl = int(parts[2])
                    except ValueError:
                        ttl = parts[2]
                cnames_dict[hostname] = {'target': target, 'ttl': ttl}

        result['hosts_config'] = hosts_dict
        result['cnames_config'] = cnames_dict

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error fetching Pi-hole configuration: {e}", **result)
    finally:
        if 'client' in locals() and client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main()
