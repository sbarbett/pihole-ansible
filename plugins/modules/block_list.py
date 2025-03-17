#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError("The 'pihole6api' Python module is required. Run 'pip install pihole6api' to install it.")

DOCUMENTATION = r'''
---
module: block_list
short_description: Manage Pi-hole block lists via pihole v6 API.
description:
    - This module adds, updates, or removes block lists on a Pi-hole instance using the piholev6api Python client.
options:
    address:
        description:
            - URL of the blocklist.
        required: true
        type: str
    state:
        description:
            - Whether the block list should be present or absent.
        required: true
        type: str
        choices: ['present', 'absent']
    comment:
        description:
            - Optional comment for the block list.
        required: false
        type: str
        default: null
    groups:
        description:
            - Optional list of group IDs. The module will validate that these groups exist.
        required: false
        type: list
        elements: int
        default: []
    enabled:
        description:
            - Whether the block list is enabled.
        required: false
        type: bool
        default: true
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
- name: Add a block list
  sbarbett.pihole.block_list:
    address: "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
    state: present
    comment: "StevenBlack hosts file"
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

- name: Update a block list with groups
  sbarbett.pihole.block_list:
    address: "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
    state: present
    comment: "StevenBlack hosts file - updated"
    groups: [0, 1]
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

- name: Remove a block list
  sbarbett.pihole.block_list:
    address: "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
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
        address=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], required=True),
        comment=dict(type='str', required=False, default=None),
        groups=dict(type='list', elements='int', required=False, default=[]),
        enabled=dict(type='bool', required=False, default=True),
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

    address = module.params['address']
    state = module.params['state']
    comment = module.params['comment']
    groups = module.params['groups']
    enabled = module.params['enabled']
    password = module.params['password']
    url = module.params['url']

    if module.check_mode:
        module.exit_json(**result)

    client = None
    try:
        client = PiHole6Client(url, password)
        lists = client.list_management
        
        # Always use 'block' as the list_type for this module
        list_type = "block"
        
        # Validate that the specified groups exist
        if groups:
            group_mgmt = client.group_management
            existing_groups_response = group_mgmt.get_groups()
            
            if 'groups' not in existing_groups_response:
                module.fail_json(msg="Failed to retrieve groups from Pi-hole", **result)
                
            existing_group_ids = [group['id'] for group in existing_groups_response['groups']]
            invalid_groups = [group_id for group_id in groups if group_id not in existing_group_ids]
            
            if invalid_groups:
                module.fail_json(
                    msg=f"The following group IDs do not exist: {invalid_groups}. Available groups: {existing_group_ids}",
                    **result
                )
        
        # Check if the block list exists
        existing_list = lists.get_list(address, list_type)
        existing_list_data = None
        
        if 'lists' in existing_list and existing_list['lists']:
            existing_list_data = existing_list['lists'][0]

        if state == 'present':
            if existing_list_data is None:
                # No list exists; add the new one
                add_response = lists.add_list(
                    address, 
                    list_type=list_type,
                    comment=comment,
                    groups=groups,
                    enabled=enabled
                )
                result['changed'] = True
                result['result'] = add_response
            else:
                # List exists, check if we need to update it
                needs_update = False
                
                # Check if any parameters need to be updated
                if (comment is not None and existing_list_data.get('comment') != comment) or \
                   (groups and set(existing_list_data.get('groups', [])) != set(groups)) or \
                   (existing_list_data.get('enabled') != enabled):
                    needs_update = True
                
                if needs_update:
                    update_response = lists.update_list(
                        address,
                        list_type=list_type,
                        comment=comment,
                        groups=groups,
                        enabled=enabled
                    )
                    result['changed'] = True
                    result['result'] = update_response
                else:
                    result['changed'] = False
                    result['result'] = {"msg": "Block list already exists with the desired configuration", "current": existing_list}

        elif state == 'absent':
            if existing_list_data is not None:
                delete_response = lists.delete_list(address, list_type=list_type)
                result['changed'] = True
                result['result'] = delete_response
            else:
                result['changed'] = False
                result['result'] = {"msg": "Block list does not exist"}

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error managing block list: {e}", **result)
    finally:
        if client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main() 