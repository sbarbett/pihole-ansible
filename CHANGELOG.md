# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.5] - YYYY-MM-DD
### Added
- `allow_list` module for adding and removing allow lists based on `state`.
- `block_list` module for adding and removing block lists based on `state`.
- `manage_lists` role for iterating over list changes and applying them to multiple PiHoles.

### Documentation
- Added examples to the `examples/` directory.
- Updated `README.md` with relevant links.

## [1.0.4] - YYYY-MM-DD
### Added
- Support for toggling Pi-hole's listening mode.

### Available Modes
- `all` - Permit all origins.
- `single` - Respond only on a specific interface.
- `bind` - Bind only to the selected interface.
- `local` - Allow only local requests.

## [1.0.2] - YYYY-MM-DD
### Added
- Clearer installation instructions for `pihole6api`.
- Support for configuring DHCP clients.
- Ability to remove DHCP leases by IP, hostname, client ID, or MAC address.

### Changed
- Moved sample playbooks to `examples/` for better structure.

## [1.0.0] - YYYY-MM-DD
### Added
- Custom modules for local A and CNAME record management with idempotent behavior.
- Role to batch process records across different Pi-hole hosts.

### Future Ideas
- Add support for teleporter.
- Docker client that auto-syncs PiHole instances.

