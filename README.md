# Skills Marketplace

A curated marketplace of Claude Code skills and plugins.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [pool-party](./pool-party) | Feature idea → clarification → planning → DAG task breakdown → parallel agent swarm |

## Installation

### Add the marketplace

```
/plugin marketplace add dylanOshima/skills
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

Each plugin lives in its own subdirectory (as a git submodule) with a standard Claude Code plugin structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
├── skills/
└── README.md
```

To add a new plugin:

1. Add the repo as a submodule: `git submodule add <repo-url> <plugin-name>`
2. Add an entry to `.claude-plugin/marketplace.json`
3. Update this README
