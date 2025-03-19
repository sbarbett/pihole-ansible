# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-03-19

### Added
- New `groups.py` module for managing Pi-hole groups
- New `clients.py` module for managing Pi-hole clients
- New `group_client_manager` role for managing groups and clients across multiple Pi-hole instances
- Example playbooks:
  - `manage-groups.yml` to demonstrate the groups module
  - `manage-clients.yml` to demonstrate the clients module
  - `manage-groups-clients.yml` to demonstrate the group_client_manager role

### Changed
- Enhanced `allow_list.py` and `block_list.py` modules to support batch processing of multiple list entries
- Modified modules to accept group names instead of requiring group IDs
- Updated the `manage_lists` role to use batch processing for better performance

## [1.0.5] - 2025-03-17
### Added
- `allow_list` module for adding and removing allow lists based on `state`.
- `block_list` module for adding and removing block lists based on `state`.
- `manage_lists` role for iterating over list changes and applying them to multiple PiHoles.

### Documentation
- Added examples to the `examples/` directory.
- Updated `README.md` with relevant links.

## [1.0.4] - 2025-02-24
### Added
- Support for toggling Pi-hole's listening mode.

### Available Modes
- `all` - Permit all origins.
- `single` - Respond only on a specific interface.
- `bind` - Bind only to the selected interface.
- `local` - Allow only local requests.

## [1.0.2] - 2025-02-23
### Added
- Clearer installation instructions for `pihole6api`.
- Support for configuring DHCP clients.
- Ability to remove DHCP leases by IP, hostname, client ID, or MAC address.

### Changed
- Moved sample playbooks to `examples/` for better structure.

## [1.0.0] - 2025-02-22
### Added
- Custom modules for local A and CNAME record management with idempotent behavior.
- Role to batch process records across different Pi-hole hosts.

### Future Ideas
- Add support for teleporter.
- Docker client that auto-syncs PiHole instances.

