#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Simon Barbett <simon@barbett.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: groups
short_description: Manage PiHole groups
description:
  - Create, update, or delete PiHole groups.
version_added: "1.0.0"
author:
  - Simon Barbett (@sbarbett)
options:
  groups:
    description:
      - List of groups to manage.
    type: list
    elements: dict
    required: true
    suboptions:
      name:
        description:
          - Name of the group.
        type: str
        required: true
      comment:
        description:
          - Comment for the group.
        type: str
        required: false
      enabled:
        description:
          - Whether the group is enabled.
          - Defaults to true if not specified.
        type: bool
        required: false
        default: true
      state:
        description:
          - Whether the group should exist or not.
        type: str
        required: true
        choices: [ present, absent ]
  url:
    description:
      - URL of the PiHole server.
    type: str
    required: true
  password:
    description:
      - Password for the PiHole server.
    type: str
    required: true
requirements:
  - pihole6api
'''

EXAMPLES = r'''
- name: Manage PiHole groups
  sbarbett.pihole.groups:
    groups:
      - name: PiHole Default
        comment: The default group
        state: present
      - name: Cameras
        enabled: false
        state: present
      - name: Default
        state: absent
      - name: IOT
        comment: IOT VLAN
        state: present
    url: "https://pihole.example.com"
    password: "admin_password"
'''

RETURN = r'''
groups:
  description: List of groups that were created, updated, or deleted.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Name of the group.
      returned: always
      type: str
      sample: PiHole Default
    comment:
      description: Comment for the group.
      returned: always
      type: str
      sample: The default group
    enabled:
      description: Whether the group is enabled.
      returned: always
      type: bool
      sample: true
    id:
      description: ID of the group.
      returned: always
      type: int
      sample: 0
    date_added:
      description: Date the group was added.
      returned: always
      type: int
      sample: 1740186106
    date_modified:
      description: Date the group was last modified.
      returned: always
      type: int
      sample: 1740186106
    state:
      description: State of the group.
      returned: always
      type: str
      sample: present
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

try:
    from pihole6api import PiHole6Client
    HAS_PIHOLE6API = True
except ImportError:
    HAS_PIHOLE6API = False


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


def create_group(client, name, comment=None, enabled=True):
    """
    Create a new group in PiHole.
    
    Args:
        client: PiHole6Client instance
        name: Name of the group
        comment: Comment for the group
        enabled: Whether the group is enabled
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.group_management.add_group(name, comment=comment, enabled=enabled)
    except Exception as e:
        return {'error': to_native(e)}


def update_group(client, name, comment=None, enabled=True):
    """
    Update an existing group in PiHole.
    
    Args:
        client: PiHole6Client instance
        name: Name of the group
        comment: Comment for the group
        enabled: Whether the group is enabled
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.group_management.update_group(name, comment=comment, enabled=enabled)
    except Exception as e:
        return {'error': to_native(e)}


def delete_group(client, name):
    """
    Delete a group from PiHole.
    
    Args:
        client: PiHole6Client instance
        name: Name of the group
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.group_management.delete_group(name)
    except Exception as e:
        return {'error': to_native(e)}


def batch_delete_groups(client, names):
    """
    Delete multiple groups from PiHole.
    
    Args:
        client: PiHole6Client instance
        names: List of group names to delete
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.group_management.batch_delete_groups(names)
    except Exception as e:
        return {'error': to_native(e)}


def main():
    module_args = dict(
        groups=dict(
            type='list',
            elements='dict',
            required=True,
            options=dict(
                name=dict(type='str', required=True),
                comment=dict(type='str', required=False, default=None),
                enabled=dict(type='bool', required=False, default=True),
                state=dict(type='str', required=True, choices=['present', 'absent']),
            ),
        ),
        url=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
    )

    result = dict(
        changed=False,
        groups=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_PIHOLE6API:
        module.fail_json(msg='The pihole6api module is required')

    url = module.params['url']
    password = module.params['password']
    groups = module.params['groups']

    client = None
    try:
        client = PiHole6Client(url, password)
        
        existing_groups = get_existing_groups(client)
        
        # Groups to delete (state: absent)
        groups_to_delete = [group['name'] for group in groups if group['state'] == 'absent' and group['name'] in existing_groups]
        
        # Process groups
        for group in groups:
            name = group['name']
            state = group['state']
            comment = group.get('comment')
            enabled = group.get('enabled', True)
            
            if state == 'present':
                if name not in existing_groups:
                    # Create new group
                    if not module.check_mode:
                        response = create_group(client, name, comment, enabled)
                        if 'error' in response:
                            module.fail_json(msg=f'Failed to create group {name}: {response["error"]}')
                    result['changed'] = True
                    result['groups'].append({
                        'name': name,
                        'comment': comment,
                        'enabled': enabled,
                        'state': 'created'
                    })
                else:
                    # Check if update is needed
                    existing = existing_groups[name]
                    update_needed = False
                    
                    if comment is not None and existing['comment'] != comment:
                        update_needed = True
                    
                    if existing['enabled'] != enabled:
                        update_needed = True
                    
                    if update_needed:
                        if not module.check_mode:
                            response = update_group(client, name, comment, enabled)
                            if 'error' in response:
                                module.fail_json(msg=f'Failed to update group {name}: {response["error"]}')
                        result['changed'] = True
                        result['groups'].append({
                            'name': name,
                            'comment': comment,
                            'enabled': enabled,
                            'state': 'updated'
                        })
                    else:
                        # No change needed
                        result['groups'].append({
                            'name': name,
                            'comment': existing['comment'],
                            'enabled': existing['enabled'],
                            'state': 'unchanged'
                        })
        
        # Delete groups
        if groups_to_delete:
            result['changed'] = True
            for name in groups_to_delete:
                result['groups'].append({
                    'name': name,
                    'state': 'deleted'
                })
            
            if not module.check_mode:
                if len(groups_to_delete) == 1:
                    response = delete_group(client, groups_to_delete[0])
                    if 'error' in response:
                        module.fail_json(msg=f'Failed to delete group {groups_to_delete[0]}: {response["error"]}')
                else:
                    response = batch_delete_groups(client, groups_to_delete)
                    if 'error' in response:
                        module.fail_json(msg=f'Failed to delete groups {", ".join(groups_to_delete)}: {response["error"]}')
        
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=f'Error managing groups: {to_native(e)}', **result)
    finally:
        if client is not None:
            client.close_session()


if __name__ == '__main__':
    main() 