#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: domains
short_description: Manage PiHole domains
description:
  - Create, update, or delete PiHole domains.
version_added: "1.0.0"
author:
  - David Hutchison (@dhutchison)
options:
  domains:
    description:
      - List of domains to manage.
    type: list
    elements: dict
    required: true
    suboptions:
      domain:
        description:
          - Domain name or list of domain names.
        type: raw
        required: true
      domain_type:
        description:
          - Type of domain.
        type: str
        required: true
        choices: [ allow, deny ]
      kind:
        description:
          - Kind of domain.
        type: str
        required: true
        choices: [ exact, regex ]
      comment:
        description:
          - Comment for the domain.
        type: str
        required: false
      groups:
        description:
          - List of group names or IDs to associate with the domain.
          - Group names will be mapped to their corresponding IDs.
        type: list
        elements: raw
        required: false
        default: []
      enabled:
        description:
          - Whether the domain is enabled.
          - Defaults to true if not specified.
        type: bool
        required: false
        default: true
      state:
        description:
          - Whether the domain should exist or not.
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
- name: Manage PiHole domains
  sbarbett.pihole.domains:
    domains:
      - domain: example.com
        domain_type: deny
        kind: exact
        comment: Block example.com
        groups:
          - Default
        enabled: true
        state: present
      - domain: [test.example.com, bad.example.com]
        domain_type: deny
        kind: regex
        comment: Block regex domains
        groups:
          - Default
        enabled: false
        state: present
      - domain: old.example.com
        domain_type: allow
        kind: exact
        state: absent
    url: "https://pihole.example.com"
    password: "admin_password"
'''

RETURN = r'''
domains:
  description: List of domains that were created, updated, or deleted.
  returned: always
  type: list
  elements: dict
  contains:
    domain:
      description: Domain name.
      returned: always
      type: str
      sample: example.com
    domain_type:
      description: Type of the domain.
      returned: always
      type: str
      sample: deny
    kind:
      description: Kind of the domain.
      returned: always
      type: str
      sample: exact
    comment:
      description: Comment for the domain.
      returned: always
      type: str
      sample: Block example.com
    enabled:
      description: Whether the domain is enabled.
      returned: always
      type: bool
      sample: true
    groups:
      description: Groups associated with the domain.
      returned: always
      type: list
      elements: raw
      sample: ["Default"]
    state:
      description: State of the domain.
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
    """
    try:
        response = client.group_management.get_groups()
        groups = response.get('groups', []) if isinstance(response, dict) else response
        return {group['name']: group for group in groups}
    except Exception:
        return {}


def map_groups_to_ids(module, group_items, existing_groups):
    """
    Map group names to their corresponding IDs.
    If a group name doesn't exist, it will be ignored with a warning.
    """
    group_ids = []
    missing_groups = []

    for item in group_items or []:
        if item is None:
            continue

        if isinstance(item, int):
            group_ids.append(item)
            continue

        found = False
        for group_name, details in existing_groups.items():
            if group_name.lower() == str(item).lower():
                group_ids.append(details['id'])
                found = True
                break

        if not found:
            missing_groups.append(str(item))

    if missing_groups:
        module.warn(f"The following groups were not found and will be ignored: {', '.join(missing_groups)}")

    return group_ids


def get_existing_domains(client):
    """
    Get existing domains from PiHole by type and kind.
    """
    existing = {}
    for domain_type in ['allow', 'deny']:
        for kind in ['exact', 'regex']:
            try:
                # This is doing a direct API call as the pihole6api doesn't handle regex domain results
                response = client.domain_management.connection.get(f"domains/{domain_type}/{kind}")
            except Exception:
                continue

            domains = []
            if isinstance(response, dict):
                if 'domains' in response and isinstance(response['domains'], list):
                    domains = response['domains']
                elif 'data' in response and isinstance(response['data'], list):
                    domains = response['data']
                elif isinstance(response.get('domain'), list):
                    domains = response.get('domain')
                elif isinstance(response.get('items'), list):
                    domains = response.get('items')
                else:
                    if 'domain' in response or 'item' in response:
                        domains = [response]
                    else:
                        for value in response.values():
                            if isinstance(value, list):
                                domains.extend(value)
            elif isinstance(response, list):
                domains = response

            for domain in domains:
                entry_domain = domain.get('domain') or domain.get('item') or domain.get('address') or domain.get('name')
                if not entry_domain:
                    continue
                key = (entry_domain, domain_type, kind)
                existing[key] = domain

    return existing


def normalize_domain_items(domains):
    normalized = []
    for item in domains:
        raw_domain = item.get('domain')
        if isinstance(raw_domain, list):
            domain_values = raw_domain
        else:
            domain_values = [raw_domain]

        for domain_value in domain_values:
            normalized.append({
                'domain': domain_value,
                'domain_type': item['domain_type'],
                'kind': item['kind'],
                'comment': item.get('comment'),
                'groups': item.get('groups', []),
                'enabled': item.get('enabled', True),
                'state': item['state'],
            })

    return normalized


def create_domain(client, domain, domain_type, kind, comment=None, groups=None, enabled=True):
    """
    Create a new domain in PiHole.
    """
    try:
        return client.domain_management.add_domain(domain, domain_type, kind, comment=comment, groups=groups, enabled=enabled)
    except Exception as e:
        return {'error': to_native(e)}


def update_domain(client, domain, domain_type, kind, comment=None, groups=None, enabled=True):
    """
    Update an existing domain in PiHole.
    """
    try:
        return client.domain_management.update_domain(domain, domain_type, kind, comment=comment, groups=groups, enabled=enabled)
    except Exception as e:
        return {'error': to_native(e)}


def delete_domain(client, domain, domain_type, kind):
    """
    Delete a domain from PiHole.
    """
    try:
        return client.domain_management.delete_domain(domain, domain_type, kind)
    except Exception as e:
        return {'error': to_native(e)}


def batch_delete_domains(client, domains):
    """
    Delete multiple domains from PiHole.
    """
    try:
        return client.domain_management.batch_delete_domains(domains)
    except Exception as e:
        return {'error': to_native(e)}


def main():
    module_args = dict(
        domains=dict(
            type='list',
            elements='dict',
            required=True,
            options=dict(
                domain=dict(type='raw', required=True),
                domain_type=dict(type='str', required=True, choices=['allow', 'deny']),
                kind=dict(type='str', required=True, choices=['exact', 'regex']),
                comment=dict(type='str', required=False, default=None),
                groups=dict(type='list', elements='raw', required=False, default=[]),
                enabled=dict(type='bool', required=False, default=True),
                state=dict(type='str', required=True, choices=['present', 'absent']),
            ),
        ),
        url=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
    )

    result = dict(
        changed=False,
        domains=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_PIHOLE6API:
        module.fail_json(msg='The pihole6api module is required')

    url = module.params['url']
    password = module.params['password']
    domains = module.params['domains']

    client = None
    try:
        client = PiHole6Client(url, password)

        existing_groups = get_existing_groups(client)
        existing_domains = get_existing_domains(client)
        normalized_domains = normalize_domain_items(domains)

        domains_to_delete = [item for item in normalized_domains
                             if item['state'] == 'absent'
                             and (item['domain'], item['domain_type'], item['kind']) in existing_domains]

        for item in normalized_domains:
            name = item['domain']
            domain_type = item['domain_type']
            kind = item['kind']
            comment = item.get('comment')
            enabled = item.get('enabled', True)
            group_ids = map_groups_to_ids(module, item.get('groups', []), existing_groups)
            key = (name, domain_type, kind)

            if item['state'] == 'present':
                if key not in existing_domains:
                    if not module.check_mode:
                        response = create_domain(client, name, domain_type, kind, comment, group_ids, enabled)
                        if 'error' in response:
                            module.fail_json(msg=f'Failed to create domain {name}: {response["error"]}')
                    result['changed'] = True
                    result['domains'].append({
                        'domain': name,
                        'domain_type': domain_type,
                        'kind': kind,
                        'comment': comment,
                        'enabled': enabled,
                        'groups': item.get('groups', []),
                        'state': 'created'
                    })
                else:
                    existing = existing_domains[key]
                    update_needed = False

                    if comment is not None and existing.get('comment') != comment:
                        update_needed = True

                    if existing.get('enabled') != enabled:
                        update_needed = True

                    existing_group_ids = set(existing.get('groups', []) or [])
                    if existing_group_ids != set(group_ids):
                        update_needed = True

                    if update_needed:
                        if not module.check_mode:
                            response = update_domain(client, name, domain_type, kind, comment, group_ids, enabled)
                            if 'error' in response:
                                module.fail_json(msg=f'Failed to update domain {name}: {response["error"]}')
                        result['changed'] = True
                        result['domains'].append({
                            'domain': name,
                            'domain_type': domain_type,
                            'kind': kind,
                            'comment': comment,
                            'enabled': enabled,
                            'groups': item.get('groups', []),
                            'state': 'updated'
                        })
                    else:
                        result['domains'].append({
                            'domain': name,
                            'domain_type': domain_type,
                            'kind': kind,
                            'comment': existing.get('comment'),
                            'enabled': existing.get('enabled'),
                            'groups': item.get('groups', []),
                            'state': 'unchanged'
                        })

        if domains_to_delete:
            result['changed'] = True
            for item in domains_to_delete:
                result['domains'].append({
                    'domain': item['domain'],
                    'domain_type': item['domain_type'],
                    'kind': item['kind'],
                    'state': 'deleted'
                })

            if not module.check_mode:
                if len(domains_to_delete) == 1:
                    response = delete_domain(client, domains_to_delete[0]['domain'],
                                             domains_to_delete[0]['domain_type'],
                                             domains_to_delete[0]['kind'])
                    if 'error' in response:
                        module.fail_json(msg=f'Failed to delete domain {domains_to_delete[0]["domain"]}: {response["error"]}')
                else:
                    delete_items = [
                        {
                            'item': item['domain'],
                            'type': item['domain_type'],
                            'kind': item['kind']
                        }
                        for item in domains_to_delete
                    ]
                    response = batch_delete_domains(client, delete_items)
                    if 'error' in response:
                        module.fail_json(msg=f'Failed to delete domains: {response["error"]}')

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=f'Error managing domains: {to_native(e)}', **result)
    finally:
        if client is not None:
            client.close_session()


if __name__ == '__main__':
    main()
