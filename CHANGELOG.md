# Changelog

All notable changes to the AstrBot Plugins Monorepo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial monorepo setup
- Combined 4 AstrBot plugins into single repository:
  - langfuse (v1.0.2)
  - discord-forwarder (v1.2.1)
  - group-geetest-verify (v1.2.3)
  - video-vision (v1.1.0)

### Changed
- Migrated plugins to packages/ directory structure
- Added shared development tooling

### Infrastructure
- Added package.json for workspace management
- Added .gitignore for Python and Node development
- Created utility scripts for plugin management
