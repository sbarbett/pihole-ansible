#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r'''
---
module: dhcp_config
version_added: "1.0.2"
short_description: Manage Pi-hole DHCP server settings via Pi-hole v6 API
description:
  - This module enables/disables the Pi-hole DHCP server and configures IPv4/IPv6 DHCP options (range, router, lease time, etc.).
  - It does NOT manage static DHCP reservations (dhcp.hosts).
  - Uses the pihole6api Python client under the hood.
options:
  url:
    description:
      - The URL of the Pi-hole instance (e.g. https://pihole.example.com).
    required: true
    type: str
  password:
    description:
      - The Pi-hole API password.
    required: true
    type: str
    no_log: true
  state:
    description:
      - If C(present), enable DHCP (active = true) and configure DHCP settings.
      - If C(absent), disable DHCP (active = false) and ignore other settings.
    required: true
    choices: [ present, absent ]
    type: str

  start:
    description:
      - The start address of the DHCP range (e.g. 10.0.6.50).
      - Required only when state=present.
    type: str
  end:
    description:
      - The end address of the DHCP range (e.g. 10.0.6.100).
      - Required only when state=present.
    type: str
  router:
    description:
      - The default gateway/router IP handed out to DHCP clients (e.g. 10.0.6.1).
      - Required only when state=present.
    type: str
  netmask:
    description:
      - Optional subnet mask in the format 255.255.255.0.
      - Leave empty to let Pi-hole infer from the Pi-hole interface IP.
    type: str
    default: ''
  lease_time:
    description:
      - DHCP lease time. Supports formats like '45m', '1h', '2d', '1w', 'infinite'.
      - Leave empty to use Pi-hole’s default.
    type: str
    default: ''
  ipv6:
    description:
      - Whether DHCPv6 (and RA) is active. Only useful if Pi-hole has an IPv6 address.
    type: bool
    default: false
  rapid_commit:
    description:
      - Enables DHCPv4 rapid commit (faster address assignment). 
      - Only enable if Pi-hole is the sole DHCP server on this network.
    type: bool
    default: false
  multi_dns:
    description:
      - Advertise Pi-hole DNS multiple times to mitigate clients adding their own DNS servers.
    type: bool
    default: false
  ignore_unknown_clients:
    description:
      - When True, Pi-hole DHCP grants addresses only to clients specifically defined in dhcp.hosts (static reservations).
      - All other clients are ignored (but can still self-assign).
    type: bool
    default: false
author:
  - Shane Barbetta (@sbarbett)
'''

EXAMPLES = r'''
- name: Enable Pi-hole DHCP with range 10.0.6.50-10.0.6.100
  sbarbett.pihole.dhcp_config:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    state: present
    start: "10.0.6.50"
    end: "10.0.6.100"
    router: "10.0.6.1"
    lease_time: "24h"

- name: Disable Pi-hole DHCP
  sbarbett.pihole.dhcp_config:
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    state: absent
'''

RETURN = r'''
changed:
  description: Whether any change was actually made to the Pi-hole config.
  type: bool
  returned: always
result:
  description: The API response or an explanation if no change occurred.
  type: dict
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Please install via 'pip install pihole6api'.")

def run_module():
    module_args = dict(
        url=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        start=dict(type='str', required=False),
        end=dict(type='str', required=False),
        router=dict(type='str', required=False),
        netmask=dict(type='str', required=False, default=''),
        lease_time=dict(type='str', required=False, default=''),
        ipv6=dict(type='bool', required=False, default=False),
        rapid_commit=dict(type='bool', required=False, default=False),
        multi_dns=dict(type='bool', required=False, default=False),
        ignore_unknown_clients=dict(type='bool', required=False, default=False),
    )

    result = dict(changed=False, result={})

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    url = module.params['url']
    password = module.params['password']
    state = module.params['state']

    start = module.params['start']
    end = module.params['end']
    router = module.params['router']
    netmask = module.params['netmask']
    lease_time = module.params['lease_time']
    ipv6 = module.params['ipv6']
    rapid_commit = module.params['rapid_commit']
    multi_dns = module.params['multi_dns']
    ignore_unknown_clients = module.params['ignore_unknown_clients']

    # If state=absent => we simply set active=False and ignore other params
    # If state=present => require start, end, router
    if state == 'present':
        missing = []
        if not start:
            missing.append('start')
        if not end:
            missing.append('end')
        if not router:
            missing.append('router')
        if missing:
            module.fail_json(msg=f"Missing required arguments for DHCP 'present': {missing}", **result)

    if module.check_mode:
        # We won't actually apply changes in check mode, but let's guess if anything would change
        # For a thorough check, we'd need to fetch current config & compare, but let's keep it simple here:
        result['changed'] = True
        module.exit_json(**result)

    # Connect to Pi-hole
    try:
        client = PiHole6Client(url, password)
    except Exception as e:
        module.fail_json(msg=f"Failed to connect to Pi-hole: {e}", **result)

    # Retrieve current DHCP config to compare
    try:
        current_config_resp = client.config.get_config_section("dhcp")
    except Exception as e:
        module.fail_json(msg=f"Failed to retrieve DHCP config: {e}", **result)

    current_dhcp = current_config_resp.get("config", {}).get("dhcp", {})

    # Build the updated settings
    if state == 'absent':
        # Just disable DHCP
        new_dhcp = dict(current_dhcp)
        new_dhcp['active'] = False
        # all other values remain as is (ignored on the Pi-hole side if active=False anyway)
    else:
        # state = 'present'
        # We want to enable DHCP and set the relevant fields
        new_dhcp = {
            'active': True,
            'start': start,
            'end': end,
            'router': router,
            'netmask': netmask,
            'leaseTime': lease_time,
            'ipv6': ipv6,
            'rapidCommit': rapid_commit,
            'multiDNS': multi_dns,
            'ignoreUnknownClients': ignore_unknown_clients,
            'hosts': current_dhcp.get('hosts', []),  # preserve existing "hosts" if any
        }
        # If you want to preserve any other fields Pi-hole might have, merge them in:
        for k in current_dhcp:
            if k not in new_dhcp:
                new_dhcp[k] = current_dhcp[k]

    # Compare old vs new
    changed = False
    for key, new_value in new_dhcp.items():
        old_value = current_dhcp.get(key)
        if old_value != new_value:
            changed = True
            break

    if not changed:
        result['changed'] = False
        result['result'] = {"msg": "No changes to DHCP configuration."}
        module.exit_json(**result)

    # If changed, send PATCH
    try:
        payload = {"dhcp": new_dhcp}
        update_resp = client.config.update_config(payload)
        result['changed'] = True
        result['result'] = update_resp
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=f"Failed to update DHCP config: {e}", **result)
    finally:
        client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main()
