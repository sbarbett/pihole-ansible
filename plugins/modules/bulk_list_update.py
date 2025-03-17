#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r"""
---
module: bulk_list_update
version_added: "1.0.5"
short_description: Manage Pi-hole Allow and Block List Settings in bulk via the Pi-hole v6 API
description:
  - This module alters the allow and block lists in bulk for a Pi-hole instance via the Pi-hole v6 API.
  - Uses the pihole6api Python client under the hood.
  - After running this command, running the gravity script is advised, because otherwise the block lists will not be applied.
options:
  url:
    description:
      - The URL of the Pi-hole instance (e.g. https://pihole.example.com).
    required: true
    type: str
  password:
    description:
      - The Pi-hole API password.
    required: true4
    type: str
    no_log: true

  lists:
    description:
        - A list of allow and block lists to set on the Pi-hole instance.
        Each List entry needs to be a dictionary with the following keys
        - address: The URL of the block list (required)
        - enabled: Whether the block list should be enabled or not (default: true, optional)
        = comment: A comment for the block list (default: "", optional)
        - groups: The group IDs to assign the block list to (default: empty list, optional)
        - type: The type of the list (block or allow) (default: block, optional)
        - state: Whether the list should be present or absent. If absent only the address parameter will be  (default: present, optional)
    required: false
    type: list
    elements: dict
    suboptions:
        address:
            description: The address of the list
            required: true
            type: str
        enabled:
            description: Whether the list should be enabled or not
            required: false
            type: bool
            default: true
        comment:
            description: A comment for the list
            required: false
            type: str
            default: ""
        groups:
            description: The group IDs to assign the list to
            required: false
            type: list
            default: []
            elements: int
        type:
            description: The type of the list (block or allow)
            required: false
            type: str
            default: block
            choices: [block, allow]
        state:
            description: Whether the list should be present or absent
            required: false
            type: str
            default: present
            choices: [present, absent]
    
author:
  - Marlena Müller (git@marlena.app)
  - Simon Barratt (@sbarratt)
"""

EXAMPLES = r"""
- name: Set block lists on Pi-hole
  sbarratt.pihole.block_lists:
    url: https://pihole.example.com
    password: mypassword
    lists:
      - address: https://example.com/blocklist.txt
        enabled: true
        comment: "This is an example block list"
        groups:
          - 0
          - 1
          - 3
        type: block
        state: present
      - address: https://example.com/blocklist2.txt
        enabled: false
        type: block
        state: present

- name: Set block lists on Pi-hole
  sbarratt.pihole.block_lists:
    url: https://pihole.example.com
    password: mypassword
    lists:
      - address: https://example.com/blocklist.txt
      - address: https://example.com/blocklist2.txt
"""

RETURN = r"""
changed:
  description: Whether any change was actually made to the Pi-hole config.
  type: bool
  returned: always
result:
  description: The API response or an explanation if no change occurred.
  type: dict
  returned: always
"""


try:
    from pihole6api import PiHole6Client
except ImportError:
    raise ImportError(
        "The 'pihole6api' Python module is required. Please install via 'pip install pihole6api'."
    )


def run_module():
    module_args = dict(
        url=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        lists=dict(
            type="list",
            required=True,
            elements="dict",
            options=dict(
                address=dict(type="str", required=True),
                enabled=dict(type="bool", required=False, default=True),
                comment=dict(type="str", required=False),
                groups=dict(type="list", required=False, default=[]),
                type=dict(type="str", required=False, default="block"),
                state=dict(type="str", required=False, default="present"),
            ),
        ),
    )

    result = dict(changed=False, result={})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    url = module.params["url"]
    password = module.params["password"]
    lists = module.params["lists"]

    if module.check_mode:
        # We won't actually apply changes in check mode, but let's guess if anything would change
        # For a thorough check, we'd need to fetch current config & compare, but let's keep it simple here:
        result["changed"] = True
        module.exit_json(**result)

    # Connect to Pi-hole
    try:
        client = PiHole6Client(url, password)
    except Exception as e:
        module.fail_json(msg=f"Failed to connect to Pi-hole: {e}", **result)

    # Retrieve current lists
    try:
        current_allow_lists = client.list_management.get_lists(list_type="allow")[
            "lists"]
        current_block_lists = client.list_management.get_lists(list_type="block")[
            "lists"]
    except Exception as e:
        module.fail_json(
            msg=f"Failed to retrieve current block lists: {e}", **result)
        
    # If no changes, return early
    if not lists:
        result["result"] = {"msg": "No block lists to update"}
        module.exit_json(**result)

    # find all new lists, that need to be added
    added_allow_lists = [
        b
        for b in lists
        if b["address"] not in [l["address"] for l in current_allow_lists] and b["type"] == "allow" and b["state"] == "present"
    ]
    added_block_lists = [
        b
        for b in lists
        if b["address"] not in [l["address"] for l in current_block_lists] and b["type"] == "block" and b["state"] == "present"
    ]

    # find all lists, that need to be removed

    removed_allow_lists = [
        b
        for b in lists
        if b["address"] in [l["address"] for l in current_allow_lists] and b["type"] == "allow" and b["state"] == "absent"
    ]
    removed_block_lists = [
        b
        for b in lists
        if b["address"] in [l["address"] for l in current_block_lists] and b["type"] == "block" and b["state"] == "absent"
    ]

    # find all lists, that need to be changed

    changed_allow_lists = []
    for b in lists:
        for l in current_allow_lists:
            # if list is already present and has the same address and rule should be present
            if b["address"] == l["address"] and b["type"] == "allow" and b["state"] == "present":
                # check if the list has changed
                if b["enabled"] != l["enabled"] or b["comment"] != l["comment"] or b["groups"] != l["groups"]:
                    changed_allow_lists.append(b)

    changed_block_lists = []
    for b in lists:
        for l in current_block_lists:
            # if list is already present and has the same address and rule should be present
            if b["address"] == l["address"] and b["type"] == "block" and b["state"] == "present":
                # check if the list has changed
                if b["enabled"] != l["enabled"] or b["comment"] != l["comment"] or b["groups"] != l["groups"]:
                    changed_block_lists.append(b)

    # If no changes, return early

    if not added_allow_lists and not added_block_lists and not removed_allow_lists and not removed_block_lists and not changed_allow_lists and not changed_block_lists:
        result["changed"] = False
        result["result"] = {"msg": "No block lists to update"}
        module.exit_json(**result)

    # Apply changes
    try:
        client.list_management.batch_delete_lists(removed_allow_lists)
        client.list_management.batch_delete_lists(removed_block_lists)

        for allow_list in added_allow_lists:
            client.list_management.add_list(
                address=allow_list["address"],
                enabled=allow_list["enabled"],
                comment=allow_list["comment"],
                groups=allow_list["groups"],
                list_type="allow",
            )

        for block_list in added_block_lists:
            client.list_management.add_list(
                address=block_list["address"],
                enabled=block_list["enabled"],
                comment=block_list["comment"],
                groups=block_list["groups"],
                list_type="block",
            )

        for allow_list in changed_allow_lists:
            client.list_management.update_list(
                address=allow_list["address"],
                enabled=allow_list["enabled"],
                comment=allow_list["comment"],
                groups=allow_list["groups"],
                list_type="allow",
            )

        for block_list in changed_block_lists:
            client.list_management.update_list(
                address=block_list["address"],
                enabled=block_list["enabled"],
                comment=block_list["comment"],
                groups=block_list["groups"],
                list_type="block",
            )

    except Exception as e:
        module.fail_json(msg=f"Failed to update block lists: {e}", **result)
    else:
        result["changed"] = True
        result["result"] = {
            "msg": f"Lists updated, removed: {len(removed_allow_lists) + len(removed_block_lists)}, added: {len(added_allow_lists) + len(added_block_lists)}, changed: {len(changed_allow_lists) + len(changed_block_lists)}"
        }
        module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
