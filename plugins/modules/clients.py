#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Simon Barbett <simon@barbett.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: clients
short_description: Manage PiHole clients
description:
  - Create, update, or delete PiHole clients.
version_added: "1.0.0"
author:
  - Simon Barbett (@sbarbett)
options:
  clients:
    description:
      - List of clients to manage.
    type: list
    elements: dict
    required: true
    suboptions:
      name:
        description:
          - The client IP address or CIDR range.
        type: str
        required: true
      comment:
        description:
          - Comment for the client.
        type: str
        required: false
      groups:
        description:
          - List of group names to assign to the client.
          - Group names will be mapped to their corresponding IDs.
        type: list
        elements: str
        required: false
        default: []
      state:
        description:
          - Whether the client should exist or not.
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
- name: Manage PiHole clients
  sbarbett.pihole.clients:
    clients:
      - name: 192.168.30.0/24
        comment: Default VLAN
        groups:
          - Default
          - test
        state: present
      - name: 192.168.40.0/24
        groups:
          - test
        state: present
      - name: 192.168.50.0/24
        state: absent
    url: "https://pihole.example.com"
    password: "admin_password"
'''

RETURN = r'''
clients:
  description: List of clients that were created, updated, or deleted.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: The client IP address or CIDR range.
      returned: always
      type: str
      sample: 192.168.30.0/24
    comment:
      description: Comment for the client.
      returned: always
      type: str
      sample: Default VLAN
    groups:
      description: List of group names assigned to the client.
      returned: always
      type: list
      elements: str
      sample: ["Default", "test"]
    state:
      description: State of the client.
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


def get_existing_clients(client):
    """
    Get existing clients from PiHole.
    
    Args:
        client: PiHole6Client instance
        
    Returns:
        dict: Mapping of client addresses to client details
    """
    try:
        response = client.client_management.get_clients()
        clients = response.get('clients', [])
        return {client_data['client']: client_data for client_data in clients}
    except Exception as e:
        return {}


def create_client(client, name, comment=None, groups=None):
    """
    Create a new client in PiHole.
    
    Args:
        client: PiHole6Client instance
        name: Client IP address or CIDR range
        comment: Comment for the client
        groups: List of group IDs
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.client_management.add_client(name, comment=comment, groups=groups or [])
    except Exception as e:
        return {'error': to_native(e)}


def update_client(client, name, comment=None, groups=None):
    """
    Update an existing client in PiHole.
    
    Args:
        client: PiHole6Client instance
        name: Client IP address or CIDR range
        comment: Comment for the client
        groups: List of group IDs
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.client_management.update_client(name, comment=comment, groups=groups or [])
    except Exception as e:
        return {'error': to_native(e)}


def delete_client(client, name):
    """
    Delete a client from PiHole.
    
    Args:
        client: PiHole6Client instance
        name: Client IP address or CIDR range
        
    Returns:
        dict: Response from the API
    """
    try:
        return client.client_management.delete_client(name)
    except Exception as e:
        return {'error': to_native(e)}


def batch_delete_clients(client, names):
    """
    Delete multiple clients from PiHole.
    
    Args:
        client: PiHole6Client instance
        names: List of client IP addresses or CIDR ranges
        
    Returns:
        dict: Response from the API
    """
    try:
        # The batch_delete_clients method expects a list of dicts with "item" key
        items = [{"item": name} for name in names]
        return client.client_management.batch_delete_clients(items)
    except Exception as e:
        return {'error': to_native(e)}


def map_groups_to_ids(module, group_names, existing_groups):
    """
    Map group names to their corresponding IDs.
    If a group name doesn't exist, it will be ignored with a warning.
    """
    group_ids = []
    missing_groups = []
    
    for name in group_names:
        # If it's already an ID (integer), add it directly
        if isinstance(name, int):
            group_ids.append(name)
            continue
            
        # Otherwise, look up the ID by name
        found = False
        for group_name, details in existing_groups.items():
            if group_name.lower() == name.lower():
                group_ids.append(details['id'])
                found = True
                break
                
        if not found:
            missing_groups.append(name)
    
    if missing_groups:
        module.warn(f"The following groups were not found and will be ignored: {', '.join(missing_groups)}")
    
    return group_ids


def main():
    module_args = dict(
        clients=dict(
            type='list',
            elements='dict',
            required=True,
            options=dict(
                name=dict(type='str', required=True),
                comment=dict(type='str', required=False, default=None),
                groups=dict(type='list', elements='str', required=False, default=[]),
                state=dict(type='str', required=True, choices=['present', 'absent']),
            ),
        ),
        url=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
    )

    result = dict(
        changed=False,
        clients=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_PIHOLE6API:
        module.fail_json(msg='The pihole6api module is required')

    url = module.params['url']
    password = module.params['password']
    clients = module.params['clients']

    client = None
    try:
        client = PiHole6Client(url, password)
        
        # Get existing groups and clients
        existing_groups = get_existing_groups(client)
        existing_clients = get_existing_clients(client)
        
        # Map group names to IDs
        group_name_to_id = {name: details['id'] for name, details in existing_groups.items()}
        
        # Clients to delete (state: absent)
        clients_to_delete = [client_data['name'] for client_data in clients 
                            if client_data['state'] == 'absent' and client_data['name'] in existing_clients]
        
        # Process clients
        for client_data in clients:
            name = client_data['name']
            state = client_data['state']
            comment = client_data.get('comment')
            group_names = client_data.get('groups', [])
            
            # Map group names to IDs
            group_ids = map_groups_to_ids(module, group_names, existing_groups)
            
            if state == 'present':
                if name not in existing_clients:
                    # Create new client
                    if not module.check_mode:
                        response = create_client(client, name, comment, group_ids)
                        if 'error' in response:
                            module.fail_json(msg=f'Failed to create client {name}: {response["error"]}')
                    result['changed'] = True
                    result['clients'].append({
                        'name': name,
                        'comment': comment,
                        'groups': group_names,
                        'state': 'created'
                    })
                else:
                    # Check if update is needed
                    existing = existing_clients[name]
                    update_needed = False
                    
                    if comment is not None and existing.get('comment') != comment:
                        update_needed = True
                    
                    # Compare group IDs
                    existing_group_ids = set(existing.get('groups', []))
                    desired_group_ids = set(group_ids)
                    if existing_group_ids != desired_group_ids:
                        update_needed = True
                    
                    if update_needed:
                        if not module.check_mode:
                            response = update_client(client, name, comment, group_ids)
                            if 'error' in response:
                                module.fail_json(msg=f'Failed to update client {name}: {response["error"]}')
                        result['changed'] = True
                        result['clients'].append({
                            'name': name,
                            'comment': comment,
                            'groups': group_names,
                            'state': 'updated'
                        })
                    else:
                        # No change needed
                        # Map existing group IDs back to names for the result
                        existing_group_names = []
                        for group_id in existing.get('groups', []):
                            for group_name, details in existing_groups.items():
                                if details['id'] == group_id:
                                    existing_group_names.append(group_name)
                                    break
                        
                        result['clients'].append({
                            'name': name,
                            'comment': existing.get('comment'),
                            'groups': existing_group_names,
                            'state': 'unchanged'
                        })
        
        # Delete clients
        if clients_to_delete:
            result['changed'] = True
            for name in clients_to_delete:
                result['clients'].append({
                    'name': name,
                    'state': 'deleted'
                })
            
            if not module.check_mode:
                if len(clients_to_delete) == 1:
                    response = delete_client(client, clients_to_delete[0])
                    if 'error' in response:
                        module.fail_json(msg=f'Failed to delete client {clients_to_delete[0]}: {response["error"]}')
                else:
                    response = batch_delete_clients(client, clients_to_delete)
                    if 'error' in response:
                        module.fail_json(msg=f'Failed to delete clients {", ".join(clients_to_delete)}: {response["error"]}')
        
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=f'Error managing clients: {to_native(e)}', **result)
    finally:
        if client is not None:
            client.close_session()


if __name__ == '__main__':
    main() 