# Development Documentation

This document provides detailed information for developers working on the AstrBot Plugins Monorepo.

## Architecture

### Monorepo Structure

```
astrbot-plugins/
├── packages/              # Plugin packages
│   ├── langfuse/         # Langfuse integration plugin
│   ├── discord-forwarder/ # Discord message forwarding
│   ├── group-geetest-verify/ # Group verification
│   └── video-vision/     # Video processing for vision
├── scripts/              # Development and maintenance scripts
├── docs/                 # Additional documentation
├── .github/              # GitHub workflows and templates
├── package.json          # Root package.json for workspace management
└── README.md             # Monorepo overview
```

### Plugin Architecture

Each plugin is an independent package that follows the AstrBot plugin architecture:

1. **Entry Point**: `main.py` contains the plugin class
2. **Metadata**: `metadata.yaml` describes the plugin
3. **Configuration**: `_conf_schema.json` defines the WebUI configuration
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

### Schema Definition

Configuration is defined in `_conf_schema.json`:

```json
{
  "type": "object",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": true
    },
    "api_key": {
      "type": "string",
      "description": "API Key for service"
    }
  }
}
```

### Accessing Configuration

```python
async def initialize(self):
    enabled = self.config.get("enabled", True)
    api_key = self.config.get("api_key", "")
```

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

### Local Testing

1. Copy plugin to AstrBot plugins directory
2. Restart AstrBot
3. Test functionality
4. Check logs for errors

### Automated Testing

The CI workflow automatically:
- Validates plugin structure
- Checks metadata.yaml format
- Validates JSON schemas
- Lints Python code

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
