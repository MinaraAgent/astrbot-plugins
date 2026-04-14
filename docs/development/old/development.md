# Development Documentation

This document provides detailed information for developers working on the AstrBot Plugins Monorepo.

## Architecture

### Monorepo Structure

```
astrbot-plugins/
├── main.py               # Meta-plugin entry point (loads all sub-plugins)
├── metadata.yaml         # Meta-plugin metadata
├── _conf_schema.json     # Unified configuration schema with namespaces
├── packages/             # Sub-plugin packages
│   ├── langfuse/         # Langfuse integration plugin
│   ├── discord-forwarder/ # Discord message forwarding
│   └── video-vision/     # Video processing for vision
├── scripts/              # Development and maintenance scripts
├── docs/                 # Additional documentation
├── .github/              # GitHub workflows and templates
├── package.json          # Root package.json for workspace management
└── README.md             # Monorepo overview
```

### Meta-Plugin Architecture

The `astrbot-plugins` monorepo uses a meta-plugin architecture:

1. **Single Installation**: Users install the meta-plugin (`astrbot-plugins`) to get all functionality
2. **Namespaced Configuration**: Each sub-plugin has its own config namespace (e.g., `langfuse.*`, `discord-forwarder.*`)
3. **Dynamic Loading**: The meta-plugin dynamically loads and manages sub-plugins
4. **Event Delegation**: The meta-plugin receives events and delegates to enabled sub-plugins
5. **Lifecycle Management**: Automatic initialization and termination of sub-plugins

### Sub-Plugin Architecture

Each sub-plugin is an independent package that follows the AstrBot plugin architecture:

1. **Entry Point**: `main.py` contains the plugin class
2. **Metadata**: `metadata.yaml` describes the plugin
3. **Configuration**: Configuration is defined in the root `_conf_schema.json` under the plugin's namespace
4. **Dependencies**: `requirements.txt` lists Python dependencies

## Plugin Lifecycle

### Initialization

```python
@register("plugin_name", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context, config)
        # Initialize plugin state

    async def initialize(self):
        # Called when plugin is loaded
        pass
```

### Event Handling

```python
@filter.command("mycommand")
async def handle_command(self, event: MessageEvent):
    # Handle command
    pass

@filter.on_llm_request()
async def on_llm_request(self, event: LLMRequestEvent):
    # Intercept LLM requests
    pass
```

### Cleanup

```python
async def terminate(self):
    # Cleanup resources
    pass
```

## Cross-Plugin Communication

Plugins can communicate using `ContextVar`:

```python
from contextvars import ContextVar

# Define shared context
shared_data = ContextVar('shared_data', default=None)

# In plugin A
shared_data.set({"key": "value"})

# In plugin B
data = shared_data.get()
```

## Configuration Management

### Namespaced Configuration

The meta-plugin provides namespaced configuration for each sub-plugin in the root `_conf_schema.json`:

```json
{
  "enabled_plugins": {
    "type": "list",
    "description": "List of enabled sub-plugins",
    "default": ["langfuse", "discord-forwarder", "video-vision"]
  },
  "langfuse": {
    "type": "object",
    "items": {
      "secret_key": {"type": "string"},
      "enabled": {"type": "bool", "default": true}
    }
  },
  "discord-forwarder": {
    "type": "object",
    "items": {
      "forward_rules": {"type": "template_list"}
    }
  }
}
```

### Accessing Configuration in Sub-Plugins

Sub-plugins receive their namespaced configuration through the meta-plugin:

```python
# In meta-plugin main.py
async def _load_sub_plugin(self, plugin_name: str) -> None:
    plugin_config = self.config.get(plugin_name, {})
    plugin_instance = plugin_class(self.context, plugin_config)
```

### Adding Configuration for a New Sub-Plugin

1. Add the namespace to `_conf_schema.json`:
```json
"my-plugin": {
  "type": "object",
  "description": "My Plugin Configuration",
  "items": {
    "enabled": {"type": "bool", "default": true},
    "api_key": {"type": "string"}
  }
}
```

2. Access the configuration in your sub-plugin:
```python
async def initialize(self):
    enabled = self.config.get("enabled", True)
    api_key = self.config.get("api_key", "")
```

## Adding a New Sub-Plugin

### Step 1: Create the Sub-Plugin Directory

```bash
mkdir packages/my-plugin
cd packages/my-plugin
```

### Step 2: Create Plugin Files

Create the standard AstrBot plugin structure:

```
packages/my-plugin/
├── main.py              # Plugin class with @register decorator
├── metadata.yaml        # Plugin metadata
├── requirements.txt     # Python dependencies
├── README.md           # Plugin documentation
└── CHANGELOG.md        # Version history
```

### Step 3: Register the Sub-Plugin

Add the sub-plugin to the `SUB_PLUGINS` dictionary in `main.py` at the root:

```python
SUB_PLUGINS = {
    # ... existing plugins
    "my-plugin": {
        "module": "packages.my-plugin.main",
        "class": "MyPlugin",
        "description": "My awesome plugin",
        "version": "1.0.0",
    },
}
```

### Step 4: Add Configuration Schema

Add the plugin's configuration namespace to `_conf_schema.json` at the root:

```json
{
  "my-plugin": {
    "type": "object",
    "description": "My Plugin Configuration",
    "items": {
      "enabled": {
        "type": "bool",
        "default": true
      },
      "api_key": {
        "type": "string"
      }
    }
  }
}
```

### Step 5: Update Documentation

- Add the plugin to `README.md`
- Update the version table
- Add plugin-specific documentation if needed

### Step 6: Test

1. Copy the entire `astrbot-plugins` directory to AstrBot's `data/plugins/`
2. Configure via WebUI or config file
3. Test the sub-plugin functionality
4. Verify that events are properly delegated

## Development Scripts

### update-all-plugins.js

Checks all plugins for version and dependency information:

```bash
npm run update:all
```

### check-dependencies.js

Analyzes dependencies across all plugins:

```bash
npm run check-deps
```

### release.js

Creates release tags for plugins:

```bash
npm run release
```

## Testing

### Local Testing Meta-Plugin

1. Copy the entire `astrbot-plugins` directory to AstrBot's `data/plugins/`:
```bash
cp -r astrbot-plugins /path/to/astrbot/data/plugins/
```

2. Configure via WebUI:
   - Open AstrBot WebUI
   - Navigate to Extensions → astrbot_plugins
   - Enable/disable sub-plugins as needed
   - Configure each sub-plugin's namespace

3. Restart AstrBot or reload plugins

4. Test functionality:
```bash
# Check meta-plugin status
/astrbot_plugins_status

# Enable/disable sub-plugins
/astrbot_plugins_enable langfuse
/astrbot_plugins_disable video-vision

# Test individual sub-plugin commands
/langfuse_status
/forward_status
/video_vision_status
```

### Local Testing Sub-Plugins Individually

Each sub-plugin can still be tested independently:

1. Navigate to the sub-plugin directory:
```bash
cd packages/[plugin-name]/
```

2. Copy to AstrBot plugins directory:
```bash
cp -r . /path/to/astrbot/data/plugins/[plugin-name]/
```

3. Configure the sub-plugin via WebUI

4. Test the sub-plugin functionality

### Automated Testing

The CI workflow automatically:
- Validates meta-plugin structure (`main.py`, `metadata.yaml`, `_conf_schema.json`)
- Validates sub-plugin structures
- Checks metadata.yaml format for all plugins
- Validates JSON schemas for all plugins
- Lints Python code for all plugins
- Tests meta-plugin loading and sub-plugin delegation

## Platform-Specific Considerations

### Discord

- Use `@filter.platform_adapter_type("discord")`
- Handle Discord-specific message types
- Support Discord's rich embeds when applicable

### Telegram

- Use `@filter.platform_adapter_type("telegram")`
- Handle Telegram's message format
- Consider Telegram's file size limits

### aiocqhttp (QQ)

- Use `@filter.platform_adapter_type("aiocqhttp")`
- Handle QQ-specific features (at messages, groups)
- Consider Chinese character encoding

## Performance Considerations

1. **Async Operations**: Always use async for I/O operations
2. **Caching**: Cache expensive operations when possible
3. **Rate Limiting**: Respect API rate limits
4. **Resource Cleanup**: Clean up temporary files and connections

## Error Handling

```python
try:
    # Operation
except SpecificException as e:
    self.logger.error(f"Error: {e}")
    # Handle error appropriately
except Exception as e:
    self.logger.exception(f"Unexpected error: {e}")
    # Fallback behavior
```

## Logging

Use AstrBot's logging system:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

## Best Practices

1. **Type Hints**: Use type hints for better code clarity
2. **Docstrings**: Document classes and functions
3. **Validation**: Validate user input
4. **Backward Compatibility**: Support legacy configurations when possible
5. **Error Messages**: Provide clear error messages
6. **Configuration**: Provide sensible defaults

## Resources

- [AstrBot Documentation](https://github.com/Soulter/AstrBot)
- [AstrBot Plugin Development Guide](https://github.com/Soulter/AstrBot/wiki)
- [Python Async Documentation](https://docs.python.org/3/library/asyncio.html)
