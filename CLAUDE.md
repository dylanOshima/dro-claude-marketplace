# Skills Marketplace

This repo is a Claude Code plugin marketplace. Each subdirectory is a plugin added as a git submodule.

## Structure

```
skills/                          # Marketplace root
├── .claude-plugin/
│   ├── plugin.json              # Marketplace manifest (name: skills-marketplace)
│   └── marketplace.json         # Registry of installable plugins
├── pool-party/                  # Git submodule → dylanOshima/pool-party
├── .gitmodules
└── README.md
```

## Adding a new plugin

1. `git submodule add <repo-url> <plugin-name>`
2. Add entry to `.claude-plugin/marketplace.json` under `plugins[]`
3. Update `README.md` table

## Conventions

- Each plugin is a git submodule with its own `.claude-plugin/plugin.json`
- Plugin names use kebab-case
