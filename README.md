# AstrBot Plugins Monorepo

A unified plugin distribution for [AstrBot](https://github.com/Soulter/AstrBot)

## Overview

This monorepo provides a **single plugin installation** that includes multiple sub-plugins. Users can install `astrbot-plugins` once and configure all sub-plugins through the AstrBot WebUI with namespaced configuration.

## Available Sub-Plugins

| Sub-Plugin | Description | Version |
|------------|-------------|---------|
| **langfuse** | Langfuse integration for LLM observability | 1.0.2 |
| **discord-forwarder** | Discord message forwarding plugin | 1.2.1 |
| **video-vision** | Video frame extraction for vision models | 1.1.0 |

## Installation

### Quick Install (Recommended)

Install the meta-plugin to get all sub-plugins at once:

1. **Install the plugin**
   - Copy the entire `astrbot-plugins` directory to your AstrBot `data/plugins/` folder
   - Or install via AstrBot WebUI (if supported)

2. **Configure via WebUI**
   - Open AstrBot WebUI
   - Navigate to Extensions → astrbot_plugins
   - Configure each sub-plugin in its namespace:
     - `enabled_plugins`: Select which sub-plugins to enable
     - `langfuse.*`: Configure Langfuse integration
     - `discord-forwarder.*`: Configure Discord forwarding rules
     - `video-vision.*`: Configure video analysis settings

3. **Restart AstrBot** (or reload plugins)

### Installing Individual Plugins

Each sub-plugin can still be installed individually if needed:

```bash
# Navigate to the specific plugin directory
cd packages/[plugin-name]/

# Copy to your AstrBot plugins directory
cp -r . /path/to/astrbot/data/plugins/[plugin-name]/
```

## Usage

### Commands

After installation, the following commands are available:

- `/astrbot_plugins_status` - Show status of all sub-plugins
- `/astrbot_plugins_enable <plugin>` - Enable a specific sub-plugin
- `/astrbot_plugins_disable <plugin>` - Disable a specific sub-plugin

Each sub-plugin also provides its own commands:
- Langfuse: `/langfuse_status`, `/langfuse_flush`
- Discord Forwarder: `/forward_status`, `/forward_test`
- Video Vision: `/video_vision_status`, `/video_vision_enable`, `/video_vision_disable`

### Configuration Example

Example configuration via WebUI:

```json
{
  "enabled_plugins": ["langfuse", "discord-forwarder", "video-vision"],
  "langfuse": {
    "enabled": true,
    "secret_key": "lfs-xxx",
    "public_key": "pk-xxx",
    "base_url": "https://cloud.langfuse.com"
  },
  "discord-forwarder": {
    "enabled": true,
    "forward_rules": [
      {
        "platform_id": "discord",
        "source_channel_id": "123456",
        "destination_channel_id": "789012",
        "enabled": true
      }
    ]
  },
  "video-vision": {
    "enabled": true,
    "max_frames": 5,
    "frame_format": "jpg"
  }
}
```

## Development

### Project Structure

```
astrbot-plugins/
├── main.py               # Meta-plugin entry point (loads all sub-plugins)
├── metadata.yaml         # Meta-plugin metadata
├── _conf_schema.json     # Unified configuration schema
├── packages/             # Sub-plugin packages
│   ├── langfuse/         # Langfuse integration
│   ├── discord-forwarder/ # Discord message forwarding
│   └── video-vision/     # Video processing for vision
├── scripts/              # Shared build and development scripts
├── docs/                 # Shared documentation
└── .github/              # GitHub workflows and templates
```

### Common Development Tasks

#### Adding a New Sub-Plugin

1. Create a new directory in `packages/`
2. Follow the standard AstrBot plugin structure:
   - `main.py` - Plugin class inheriting from `Star`
   - `metadata.yaml` - Plugin metadata
   - `requirements.txt` - Python dependencies
3. Add the sub-plugin to `main.py` in the `SUB_PLUGINS` dictionary
4. Add the plugin's configuration to `_conf_schema.json` under a new namespace
5. Update this README with the new plugin information

#### Updating Sub-Plugins

```bash
# Update a specific sub-plugin
cd packages/[plugin-name]
# Make changes and commit

# Update all sub-plugins (run from root)
npm run update:all
```

#### Running Tests

```bash
# Run tests for all sub-plugins
npm test

# Run tests for a specific sub-plugin
npm test --workspace=packages/[plugin-name]
```

### Plugin Development Guidelines

All sub-plugins in this repository follow the AstrBot plugin standard:

- **main.py** - Main plugin code with `@register` decorator
- **metadata.yaml** - Plugin metadata (name, author, version, description)
- **requirements.txt** - Python dependencies
- **README.md** - Plugin documentation
- **CHANGELOG.md** - Version history

The meta-plugin provides:
- Unified entry point via `main.py` at the root
- Namespaced configuration via `_conf_schema.json`
- Automatic loading and lifecycle management for all sub-plugins
- Event delegation to enabled sub-plugins

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

Each plugin may have its own license. Please refer to the individual plugin directories for license information.

## Links

- [AstrBot Documentation](https://github.com/Soulter/AstrBot)
- [MinaraAgent GitHub](https://github.com/MinaraAgent)
- [Development Documentation](./docs/development.md)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for repository-level changes.

## Architecture

### Meta-Plugin Design

The `astrbot-plugins` meta-plugin provides:

1. **Single Installation**: Users install one plugin to get all functionality
2. **Namespaced Configuration**: Each sub-plugin has its own config namespace
3. **Independent Enable/Disable**: Users can enable specific sub-plugins via WebUI
4. **Event Delegation**: The meta-plugin receives events and delegates to enabled sub-plugins
5. **Lifecycle Management**: Automatic initialization and termination of sub-plugins

### Configuration Flow

```
User (WebUI)
    ↓
astrbot_plugins (meta-plugin)
    ├── enabled_plugins: ["langfuse", "discord-forwarder"]
    ├── langfuse.*
    ├── discord-forwarder.*
    └── video-vision.*
    ↓
Sub-plugins (loaded and managed by meta-plugin)
```

This design follows the AstrBot plugin standard while providing a unified experience for users and easier maintenance for developers.
