# CLAUDE.md

## Project Overview

a plugin group, manage all plugins of mine in one place

## Repository Structure

```
.
├── .claude/                                    # Claude Code configuration
│   └── settings.local.json                    # Local Claude Code settings
├── .github/                                   # GitHub configuration
├── code-repo/                                 # Storage for cloned code repositories
│   └── github/                                # Public GitHub repositories
│       └── AstrBot/                           # AstrBot repository
├── data/                                      # Persistent data storage for the workspace
├── debug/                                     # Temporary debugging files ONLY
├── docs/                                      # Project documentation
│   |── development/                           # Date-based development plans (YY-MM-DD/)
│   |   ├── 26-04-12/                          # Development notes for Apr 12, 2026
│   |   └── old/                               # Archived development notes
│   └── project
│       └── verify.md                          # what the behavior of the repo should be
├── packages/                                  # Plugin packages
│   ├── __init__.py                            # Package initialization
│   ├── discord-forwarder/                     # Discord message forwarder plugin
│   │   ├── __init__.py                        # Plugin initialization
│   │   ├── main.py                            # Plugin main logic
│   │   ├── metadata.yaml                      # Plugin metadata
│   │   ├── _conf_schema.json                  # Configuration schema
│   │   ├── requirements.txt                   # Python dependencies
│   │   ├── README.md                          # Plugin documentation
│   │   └── CHANGELOG.md                       # Plugin changelog
│   ├── langfuse/                              # Langfuse integration plugin
│   │   ├── __init__.py                        # Plugin initialization
│   │   ├── main.py                            # Plugin main logic
│   │   ├── metadata.yaml                      # Plugin metadata
│   │   ├── _conf_schema.json                  # Configuration schema
│   │   ├── requirements.txt                   # Python dependencies
│   │   ├── README.md                          # Plugin documentation
│   │   └── CHANGELOG.md                       # Plugin changelog
│   └── video-vision/                          # Video vision analysis plugin
│       ├── __init__.py                        # Plugin initialization
│       ├── main.py                            # Plugin main logic
│       ├── metadata.yaml                      # Plugin metadata
│       ├── _conf_schema.json                  # Configuration schema
│       ├── requirements.txt                   # Python dependencies
│       ├── README.md                          # Plugin documentation
│       └── CHANGELOG.md                       # Plugin changelog
├── scripts/                                   # Repository scripts
│   ├── check-dependencies.js                  # Dependency checker
│   ├── release.js                             # Release automation
│   └── update-all-plugins.js                  # Plugin update script
├── .gitignore                                 # Git ignore file
├── CHANGELOG.md                               # Project changelog
├── CLAUDE.md                                  # Project overview and guidelines for AI agents
├── CONTRIBUTING.md                            # Contribution guidelines
├── LICENSE                                    # License file
├── README.md                                  # Project README file
├── _conf_schema.json                          # Global configuration schema
├── main.py                                    # Main plugin entry point
├── metadata.yaml                              # Project metadata
├── package.json                               # Node.js package configuration
└── requirements.txt                           # Python dependencies
```

## Development Workflow

### Date-Based Organization

- Development notes: `docs/development/YY-MM-DD/`
- AI summaries: `.ai/summaries/YY-MM-DD/`
- Use this format for all new development work

### Context Sources (in priority order)

1. `docs/development/` - Current plans and architecture
2. `docs/TODO.md` - Pending work
3. `.ai/summaries/` - Past AI work and decisions
4. `docs/AI-external-context/` - External system context

### File Organization Rules

- All scripts → `scripts/`
- Temporary debugging → `debug/` (never commit this)
- Documentation → `docs/development/YY-MM-DD/`

## Important Notes

2. **Always check `docs/development/`** for current plans before implementing
3. **Date-based file organization** for all new documentation
4. **TODO.md is for unfinished tasks only** - remove completed items
