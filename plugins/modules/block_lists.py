#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: block_lists
version_added: "1.0.5"
short_description: Manage Pi-hole Block List Settings via the Pi-hole v6 API
description:
  - This module sets the block lists for a Pi-hole instance via the Pi-hole v6 API.
  - Uses the pihole6api Python client under the hood.
  - After running this command, running the gravity script is adviced, becaus otherwise the block lists will not be applied.
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

  block_lists:
    description:
        - A list of block lists to set on the Pi-hole instance.
        Each List entry needs to be a dictionary with the following keys
        - address: The URL of the block list (required)
        - enabled: Whether the block list should be enabled or not (default: true, optional)
        = comment: A comment for the block list (default: "", optional)
        - groups: The group IDs to assign the block list to (default: empty list, optional)
    required: false
    type: list
    elements: dict
    suboptions:
        address:
            description: The address of the block list
            required: true
            type: str
        enabled:
            description: Whether the block list should be enabled or not
            required: false
            type: bool
            default: true
        comment:
            description: A comment for the block list
            required: false
            type: str
            default: ""
        groups:
            description: The group IDs to assign the block list to
            required: false
            type: list
            default: []
            elements: str
    
    
author:
  - Marlena Müller (git@marlena.app)
"""

EXAMPLES = r"""
- name: Set block lists on Pi-hole
  sbarratt.pihole.block_lists:
    url: https://pihole.example.com
    password: mypassword
    block_lists:
        - address: https://example.com/blocklist.txt
          enabled: true
          comment: "This is an example block list"
          group: "Example Group"
        - address: https://example.com/blocklist2.txt
          enabled: false
          group: "Example Group"

- name: Set block lists on Pi-hole
  sbarratt.pihole.block_lists:
    url: https://pihole.example.com
    password: mypassword
    block_lists:
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

from ansible.module_utils.basic import AnsibleModule

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
        block_lists=dict(
            type="list",
            required=True,
            elements="dict",
            options=dict(
                address=dict(type="str", required=True),
                enabled=dict(type="bool", required=False, default=True),
                comment=dict(type="str", required=False),
                group=dict(type="str", required=False, default="Default"),
            ),
        ),
    )

    result = dict(changed=False, result={})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    url = module.params["url"]
    password = module.params["password"]
    block_lists = module.params["block_lists"]

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

    # Retrieve current block lists
    try:
        current_block_lists = client.list_management.get_lists(list_type="block")[
            "lists"
        ]
    except Exception as e:
        module.fail_json(msg=f"Failed to retrieve current block lists: {e}", **result)

    print(current_block_lists)

    # Add default values to block lists

    for block_list in block_lists:
        if "enabled" not in block_list:
            block_list["enabled"] = True
        if "comment" not in block_list:
            block_list["comment"] = ""
        if "groups" not in block_list:
            block_list["groups"] = []

    # find all removed block lists (i.e. lists that are in current_block_lists but not in block_lists)
    removed_block_lists = [
        l
        for l in current_block_lists
        if l["address"] not in [b["address"] for b in block_lists]
    ]

    # find all added block lists (i.e. lists that are in block_lists but not in current_block_lists)
    added_block_lists = [
        b
        for b in block_lists
        if b["address"] not in [l["address"] for l in current_block_lists]
    ]

    # find all changed block lists (i.e. lists that are in both current_block_lists and block_lists but have different values)
    changed_block_lists = [
        b
        for b in block_lists
        if b["address"] in [l["address"] for l in current_block_lists]
        and any(
            b[k] != l[k] for k in b.keys() for l in current_block_lists if k in l.keys()
        )
    ]

    # If no changes, return early
    if not removed_block_lists and not added_block_lists and not changed_block_lists:
        result["changed"] = False
        result["result"] = {"msg": "No changes required"}
        module.exit_json(**result)

    removed_block_lists = [
        {"address": l["address"], type: "block"} for l in removed_block_lists
    ]

    # Apply changes
    try:
        client.list_management.batch_delete_lists(removed_block_lists)

        for block_list in added_block_lists:
            client.list_management.add_list(
                address=block_list["address"],
                list_type="block",
                comment=block_list["comment"],
                groups=block_list["groups"],
                enabled=block_list["enabled"],
            )

        for block_list in changed_block_lists:
            client.list_management.update_list(
                address=block_list["address"],
                list_type="block",
                comment=block_list["comment"],
                groups=block_list["groups"],
                enabled=block_list["enabled"],
            )

    except Exception as e:
        module.fail_json(msg=f"Failed to update block lists: {e}", **result)
    else:
        result["changed"] = True
        result["result"] = {
            "msg": "Block lists updated, removed: {}, added: {}, changed: {}".format(
                len(removed_block_lists),
                len(added_block_lists),
                len(changed_block_lists),
            )
        }
        module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
