# Skills Marketplace

This repo is the primary Claude Code plugin marketplace. Plugins can live directly in this repo as subdirectories or be linked as git submodules for externally-hosted plugins.

## Structure

```
skills/                          # Marketplace root
├── .claude-plugin/
│   ├── plugin.json              # Marketplace manifest (name: skills-marketplace)
│   └── marketplace.json         # Registry of installable plugins
├── pool-party/                  # Git submodule → dylanOshima/pool-party
├── remember-that/               # Local plugin (lives in this repo)
├── .gitmodules
└── README.md
```

## Adding a new plugin

Plugins can be added in two ways:

### Local plugin (default)
1. Create a subdirectory with kebab-case name
2. Add a `.claude-plugin/plugin.json` inside it
3. Add entry to `.claude-plugin/marketplace.json` under `plugins[]`
4. Update `README.md` table

### External plugin (git submodule)
1. `git submodule add <repo-url> <plugin-name>`
2. Add entry to `.claude-plugin/marketplace.json` under `plugins[]`
3. Update `README.md` table

## Conventions

- Plugin names use kebab-case
- Each plugin has its own `.claude-plugin/plugin.json`
- Plugins can be local directories or git submodules
- **When creating a new plugin or skill, always register it in `.claude-plugin/marketplace.json` and update `README.md`**
