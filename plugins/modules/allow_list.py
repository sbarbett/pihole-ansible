#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

try:
    from pihole6api import PiHole6Client
    HAS_PIHOLE6API = True
except ImportError:
    HAS_PIHOLE6API = False

DOCUMENTATION = r'''
---
module: allow_list
short_description: Manage Pi-hole allow lists via pihole v6 API.
description:
    - This module adds, updates, or removes allow lists on a Pi-hole instance using the piholev6api Python client.
    - Supports batch processing of multiple allow list entries.
    - Maps group names to their corresponding IDs.
options:
    lists:
        description:
            - List of allow list entries to manage.
        required: false
        type: list
        elements: dict
        suboptions:
            address:
                description:
                    - URL of the allowlist.
                required: true
                type: str
            state:
                description:
                    - Whether the allow list should be present or absent.
                required: true
                type: str
                choices: ['present', 'absent']
            comment:
                description:
                    - Optional comment for the allow list.
                required: false
                type: str
                default: null
            groups:
                description:
                    - Optional list of group names. The module will map these to group IDs.
                required: false
                type: list
                elements: str
                default: []
            enabled:
                description:
                    - Whether the allow list is enabled.
                required: false
                type: bool
                default: true
    address:
        description:
            - URL of the allowlist. For backward compatibility.
            - If both 'lists' and 'address' are provided, 'lists' takes precedence.
        required: false
        type: str
    state:
        description:
            - Whether the allow list should be present or absent. For backward compatibility.
        required: false
        type: str
        choices: ['present', 'absent']
    comment:
        description:
            - Optional comment for the allow list. For backward compatibility.
        required: false
        type: str
        default: null
    groups:
        description:
            - Optional list of group IDs or names. For backward compatibility.
            - If providing group IDs, they must be integers.
            - If providing group names, they will be mapped to their corresponding IDs.
        required: false
        type: list
        elements: raw
        default: []
    enabled:
        description:
            - Whether the allow list is enabled. For backward compatibility.
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
    update_gravity:
        description:
            - Whether to run gravity after making changes.
        required: false
        type: bool
        default: false
author:
    - Shane Barbetta (@sbarbett)
'''

EXAMPLES = r'''
# Batch processing with group names
- name: Manage multiple allow lists
  sbarbett.pihole.allow_list:
    lists:
      - address: "https://example.com/whitelist1.txt"
        state: present
        comment: "Example whitelist 1"
        groups:
          - Default
          - test
      - address: "https://example.com/whitelist2.txt"
        state: present
        comment: "Example whitelist 2"
        groups:
          - Default
      - address: "https://example.com/whitelist3.txt"
        state: absent
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

# Legacy single entry format (still supported)
- name: Add an allow list
  sbarbett.pihole.allow_list:
    address: "https://example.com/whitelist.txt"
    state: present
    comment: "Example whitelist"
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

- name: Update an allow list with group IDs (legacy)
  sbarbett.pihole.allow_list:
    address: "https://example.com/whitelist.txt"
    state: present
    comment: "Example whitelist - updated"
    groups: [0, 1]
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"

- name: Update an allow list with group names and run gravity
  sbarbett.pihole.allow_list:
    address: "https://example.com/whitelist.txt"
    state: present
    comment: "Example whitelist - updated"
    groups: ["Default", "test"]
    url: "https://your-pihole.example.com"
    password: "{{ pihole_password }}"
    update_gravity: true
'''

RETURN = r'''
result:
    description: The API responses from the Pi-hole server.
    type: dict
    returned: always
changed:
    description: Whether any change was made.
    type: bool
    returned: always
'''

def get_existing_groups(client):
    """
    Get existing groups from PiHole.
    
    Args:
        client: PiHole6Client instance
        
    Returns:
        dict: Mapping of group names to group details
    """
    try:
        response = client.group_management.get_groups()
        groups = response.get('groups', [])
        return {group['name']: group for group in groups}
    except Exception as e:
        return {}

def map_groups_to_ids(module, group_items, existing_groups):
    """
    Map group names to their corresponding IDs.
    If a group name doesn't exist, it will be ignored with a warning.
    """
    group_ids = []
    missing_groups = []
    
    for item in group_items:
        # If it's already an ID (integer), add it directly
        if isinstance(item, int):
            group_ids.append(item)
            continue
            
        # Otherwise, look up the ID by name
        found = False
        for group_name, details in existing_groups.items():
            if group_name.lower() == item.lower():
                group_ids.append(details['id'])
                found = True
                break
                
        if not found:
            missing_groups.append(item)
    
    if missing_groups:
        module.warn(f"The following groups were not found and will be ignored: {', '.join(missing_groups)}")
    
    return group_ids

def run_module():
    module_args = dict(
        lists=dict(
            type='list',
            elements='dict',
            required=False,
            options=dict(
                address=dict(type='str', required=True),
                state=dict(type='str', choices=['present', 'absent'], required=True),
                comment=dict(type='str', required=False, default=None),
                groups=dict(type='list', elements='str', required=False, default=[]),
                enabled=dict(type='bool', required=False, default=True),
            ),
        ),
        # Legacy parameters for backward compatibility
        address=dict(type='str', required=False),
        state=dict(type='str', choices=['present', 'absent'], required=False),
        comment=dict(type='str', required=False, default=None),
        groups=dict(type='list', elements='raw', required=False, default=[]),
        enabled=dict(type='bool', required=False, default=True),
        password=dict(type='str', required=True, no_log=True),
        url=dict(type='str', required=True),
        update_gravity=dict(type='bool', required=False, default=False)
    )

    result = dict(
        changed=False,
        result={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[['lists', 'address']],
        required_by={'address': ['state']}
    )

    password = module.params['password']
    url = module.params['url']
    update_gravity = module.params.get('update_gravity', False)
    
    # Check if we're using the new lists parameter or legacy parameters
    lists_param = module.params['lists']
    
    # If lists parameter is not provided, create a single-item list from legacy parameters
    if not lists_param:
        address = module.params['address']
        state = module.params['state']
        comment = module.params['comment']
        groups = module.params['groups']
        enabled = module.params['enabled']
        
        lists_param = [{
            'address': address,
            'state': state,
            'comment': comment,
            'groups': groups,
            'enabled': enabled
        }]

    if module.check_mode:
        module.exit_json(**result)

    if not HAS_PIHOLE6API:
        module.fail_json(msg='The pihole6api module is required')

    client = None
    try:
        client = PiHole6Client(url, password)
        lists = client.list_management
        
        # Always use 'allow' as the list_type for this module
        list_type = "allow"
        
        # Get existing groups for mapping
        existing_groups = get_existing_groups(client)
        
        # Lists to delete (state: absent)
        lists_to_delete = []
        
        # Process each list item
        processed_results = []
        
        for list_item in lists_param:
            address = list_item['address']
            state = list_item['state']
            comment = list_item.get('comment')
            group_items = list_item.get('groups', [])
            enabled = list_item.get('enabled', True)
            
            # Map group names/IDs to group IDs
            groups = map_groups_to_ids(module, group_items, existing_groups)
            
            # Check if the allow list exists
            existing_list = lists.get_list(address, list_type)
            existing_list_data = None
            
            if 'lists' in existing_list and existing_list['lists']:
                existing_list_data = existing_list['lists'][0]

            if state == 'present':
                if existing_list_data is None:
                    # No list exists; add the new one
                    if not module.check_mode:
                        add_response = lists.add_list(
                            address, 
                            list_type=list_type,
                            comment=comment,
                            groups=groups,
                            enabled=enabled
                        )
                        processed_results.append({
                            'address': address,
                            'action': 'added',
                            'response': add_response
                        })
                    result['changed'] = True
                else:
                    # List exists, check if we need to update it
                    needs_update = False
                    
                    # Check if any parameters need to be updated
                    if (comment is not None and existing_list_data.get('comment') != comment) or \
                       (groups and set(existing_list_data.get('groups', [])) != set(groups)) or \
                       (existing_list_data.get('enabled') != enabled):
                        needs_update = True
                    
                    if needs_update:
                        if not module.check_mode:
                            update_response = lists.update_list(
                                address,
                                list_type=list_type,
                                comment=comment,
                                groups=groups,
                                enabled=enabled
                            )
                            processed_results.append({
                                'address': address,
                                'action': 'updated',
                                'response': update_response
                            })
                        result['changed'] = True
                    else:
                        processed_results.append({
                            'address': address,
                            'action': 'unchanged',
                            'current': existing_list
                        })

            elif state == 'absent':
                if existing_list_data is not None:
                    lists_to_delete.append(address)
                    processed_results.append({
                        'address': address,
                        'action': 'marked_for_deletion'
                    })
                    result['changed'] = True
                else:
                    processed_results.append({
                        'address': address,
                        'action': 'absent_already'
                    })
        
        # Process deletions
        if lists_to_delete:
            if not module.check_mode:
                # TODO: If batch_delete_lists is available in the API, use it here
                # For now, delete one by one
                for address in lists_to_delete:
                    delete_response = lists.delete_list(address, list_type=list_type)
                    # Update the corresponding result in processed_results
                    for item in processed_results:
                        if item['address'] == address and item['action'] == 'marked_for_deletion':
                            item['action'] = 'deleted'
                            item['response'] = delete_response

        if update_gravity:
            client.connection.connection_timeout = 60  # Set a timeout for the gravity run
            res = client.actions.run_gravity()
            if "List has been updated" in res:
                result['changed'] = True
            processed_results.append(
                {
                    'action': 'run_gravity',
                    'response': res,
                }
            )

        result['result'] = processed_results
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error managing allow lists: {to_native(e)}", **result)
    finally:
        if client is not None:
            client.close_session()

def main():
    run_module()

if __name__ == '__main__':
    main() 