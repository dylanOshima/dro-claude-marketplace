# Brandy

Interactive brand creation and design system generation for web and mobile apps.

## What it does

Brandy guides you through creating a complete brand identity and design system through a collaborative, visual workflow. It uses a browser-based preview to show mockups, color palettes, typography specimens, and design directions — letting you click to select preferences and iterate in real time.

## Commands

### `/brandy:bootstrap`

Creates a brand and design system from scratch or by analyzing an existing codebase.

**Flow:**
1. **Clarifier** — understands your product, audience, and goals
2. **Brand Strategist** — defines positioning, personality, values, tone
3. **Creative Director** — proposes 2-3 visual directions (shown in browser)
4. **Designer** — applies the brand to realistic UI mockups
5. **Design System Architect** — converts designs into tokens and component specs
6. **System Integrator** — exports all deliverables

**Output:**
```
brand/
├── brand-guide.md
├── design-system.md
├── tokens/
│   ├── tokens.json
│   ├── tokens.css
│   ├── _tokens.scss
│   └── tailwind.tokens.js
├── assets/
│   ├── logo-primary.svg
│   ├── logo-mark.svg
│   └── logo-wordmark.svg
└── README.md
```

### `/brandy:generate`

Generates specific assets from an existing brandy brand output.

**Supported assets:**
- App icons (iOS xcassets, Android mipmap, web favicons)
- Logo variants (SVG + PNG exports)
- Color palette swatches with accessibility report
- Design tokens (JSON, CSS, SCSS, Tailwind)
- Typography specimen pages
- Text content (taglines, microcopy, tone examples)

## Requirements

- **Node.js** — for the preview server
- **librsvg** (`brew install librsvg`) or **Inkscape** — for SVG-to-PNG icon export
- **jq** — for JSON processing in export scripts

## Installation

```bash
claude plugin install skills-marketplace@brandy
```

Or test locally:
```bash
claude --plugin-dir /path/to/brand-design
```
