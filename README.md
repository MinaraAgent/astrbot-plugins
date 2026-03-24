# AstrBot Plugins Monorepo

This repository contains a collection of [AstrBot](https://github.com/Soulter/AstrBot) plugins maintained by [MinaraAgent](https://github.com/MinaraAgent).

## Overview

This monorepo consolidates multiple AstrBot plugins into a single repository for easier maintenance, development, and updates.

## Available Plugins

| Plugin | Description | Version |
|--------|-------------|---------|
| [langfuse](./packages/langfuse) | Langfuse integration for LLM observability | 1.0.2 |
| [discord-forwarder](./packages/discord-forwarder) | Discord message forwarding plugin | 1.2.1 |
| [group-geetest-verify](./packages/group-geetest-verify) | Group join verification with GeeTest | 1.2.3 |
| [video-vision](./packages/video-vision) | Video frame extraction for vision models | 1.1.0 |

## Installation

### Installing Individual Plugins

Each plugin can be installed individually. Navigate to the plugin directory:

```bash
cd packages/[plugin-name]
```

Then follow the installation instructions in the plugin's README.

### Installing All Plugins

To install all plugins at once (for development purposes):

```bash
# Install all dependencies
pnpm install

# Or using npm
npm install
```

## Development

### Project Structure

```
astrbot-plugins/
├── packages/              # Individual plugin packages
│   ├── langfuse/         # Langfuse integration
│   ├── discord-forwarder/ # Discord message forwarding
│   ├── group-geetest-verify/ # Group verification
│   └── video-vision/     # Video processing for vision
├── scripts/              # Shared build and development scripts
├── docs/                 # Shared documentation
├── .github/              # GitHub workflows and templates
├── README.md             # This file
└── package.json          # Root package.json for workspace management
```

### Common Development Tasks

#### Adding a New Plugin

1. Create a new directory in `packages/`
2. Follow the standard AstrBot plugin structure
3. Add the plugin to this README
4. Update the root `package.json` if needed

#### Updating Plugins

```bash
# Update a specific plugin
cd packages/[plugin-name]
# Make changes and commit

# Update all plugins (run from root)
npm run update:all
```

#### Running Tests

```bash
# Run tests for all plugins
npm test

# Run tests for a specific plugin
npm test --workspace=packages/[plugin-name]
```

## Plugin Development Guidelines

All plugins in this repository follow the AstrBot plugin structure:

- `main.py` - Main plugin code
- `metadata.yaml` - Plugin metadata
- `requirements.txt` - Python dependencies
- `_conf_schema.json` - Configuration schema for WebUI
- `README.md` - Plugin documentation
- `CHANGELOG.md` - Version history

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

Each plugin may have its own license. Please refer to the individual plugin directories for license information.

## Links

- [AstrBot Documentation](https://github.com/Soulter/AstrBot)
- [MinaraAgent GitHub](https://github.com/MinaraAgent)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for repository-level changes.
