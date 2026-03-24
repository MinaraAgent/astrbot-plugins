# Contributing to AstrBot Plugins Monorepo

Thank you for your interest in contributing to this monorepo! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (for development scripts)
- Git
- AstrBot installation for testing

### Setting Up Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/astrbot-plugins.git
   cd astrbot-plugins
   ```

2. Install development dependencies:
   ```bash
   npm install
   ```

3. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

## Plugin Structure

All plugins must follow the standard AstrBot plugin structure:

```
packages/plugin-name/
├── main.py                    # Required: Main plugin code
├── metadata.yaml              # Required: Plugin metadata
├── requirements.txt           # Optional: Python dependencies
├── _conf_schema.json          # Required: Configuration schema
├── README.md                  # Required: Documentation
├── CHANGELOG.md               # Recommended: Version history
└── [assets]/                  # Optional: Images, logos, etc.
```

## Adding a New Plugin

1. Create a new directory in `packages/`
2. Follow the standard plugin structure
3. Update this monorepo's README.md to include your plugin
4. Ensure all required files are present
5. Test thoroughly with AstrBot

### metadata.yaml Requirements

```yaml
name: astrbot_plugin_name       # Required, must start with astrbot_plugin_
display_name: Display Name      # Human-readable name
desc: Short description          # Plugin description
version: 1.0.0                  # SemVer version
author: Your Name               # Author name
repo: https://github.com/...    # Repository URL
support_platforms:               # Optional platform restrictions
  - discord
astrbot_version: ">=4.16,<5"     # AstrBot version compatibility
```

### _conf_schema.json Requirements

Configuration schemas must be valid JSON and follow the AstrBot WebUI schema format.

## Development Workflow

### Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test locally

3. Run development scripts:
   ```bash
   npm run check-deps    # Check dependencies
   npm run lint          # Lint code
   ```

### Commit Messages

Follow conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

Example:
```
feat(langfuse): add session timeout configuration
```

### Pull Requests

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a pull request with:
   - Clear description of changes
   - Related issue numbers
   - Screenshots for UI changes
   - Testing instructions

3. Wait for review and address feedback

## Coding Standards

### Python Code

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to classes and functions
- Handle errors gracefully
- Log important events

### Configuration

- Use clear, descriptive configuration keys
- Provide sensible defaults
- Include help text in _conf_schema.json
- Validate user input

## Testing

Test your changes with:
1. Different AstrBot versions (if applicable)
2. Different platforms (Discord, Telegram, etc.)
3. Edge cases and error conditions
4. Multiple concurrent users/sessions

## Release Process

Releases are handled by maintainers using the release script:
```bash
npm run release
```

This creates git tags for each plugin version that can be published to GitHub.

## Questions?

Feel free to:
- Open an issue for questions or problems
- Join our community discussions
- Contact maintainers directly

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
