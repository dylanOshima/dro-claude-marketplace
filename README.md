# Skills Marketplace

A curated marketplace of Claude Code skills and plugins.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [pool-party](./pool-party) | Feature idea → clarification → planning → DAG task breakdown → parallel agent swarm |
| [remember-that](./remember-that) | Reflect on sessions and persist learnings to the right documentation |
| [brandy](./brand-design) | Interactive brand creation and design system generation for web and mobile apps |

## Installation

### Add the marketplace

```
/plugin marketplace add dylanOshima/dro-claude-marketplace
```

### Browse available skills

```
/browse
```

### Install a plugin

```
/install-skill pool-party
```

Or directly via CLI:

```bash
claude plugin install skills-marketplace@pool-party
```

## Adding a Plugin

Each plugin lives in its own subdirectory with a standard Claude Code plugin structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
├── skills/
└── README.md
```

Plugins can be added as local directories (default) or as git submodules for externally-hosted repos.

To add a new plugin:

1. Create a subdirectory (or `git submodule add` for external repos)
2. Add an entry to `.claude-plugin/marketplace.json`
3. Update this README
