---
name: generate
description: This skill should be used when the user asks to "generate brand assets", "export icons", "create app icons", "generate logos", "export design tokens", "create color palette", "generate typography specimen", "create text content", "brandy generate", or invokes /brandy:generate. Generates specific assets from an existing brandy brand output.
---

# Brandy Generate

Generate specific brand assets from an existing brandy brand output.

## Overview

Generate reads the existing brand output (brand guide, design tokens, visual identity) and produces specific assets the user requests. It uses the clarifier agent to understand requirements, shows previews in the browser, and runs programmatic scripts for export.

## Supported Asset Types

1. **Icons** — app icons exported at multiple sizes for web, iOS (xcassets), and Android (mipmap)
2. **Logos** — SVG variants (primary, mark, wordmark) + PNG exports at specified sizes
3. **Color palette** — visual swatch sheet with accessibility contrast report
4. **Design tokens** — JSON, CSS custom properties, SCSS variables, Tailwind config
5. **Typography specimen** — preview page showing the type system in use
6. **App icon sets** — complete icon sets for iOS, Android, and web (favicon + PWA)
7. **Text content** — taglines, microcopy, tone-of-voice examples based on brand strategy

## Checklist

1. **Locate brand output** — find existing brandy output directory
2. **Run clarifier** — understand what assets the user wants
3. **Start preview server** — for visual review before export
4. **Generate preview** — create and show preview of the requested assets
5. **Iterate** — refine based on user feedback
6. **Export** — run scripts to produce final assets
7. **Stop preview server** — clean up

## Process

### Step 1: Locate Brand Output

Search for existing brand output:
- Check `brand/` at the project root (default)
- Check for `tokens.json`, `brand-guide.md`, or `design-system.md`
- If not found, ask the user for the path
- If no brand output exists at all, suggest running `/brandy:bootstrap` first

Read the brand guide and tokens to understand the current brand system.

### Step 2: Run Clarifier

Dispatch the `brandy-clarifier` agent in generate mode with:
- The user's request
- The existing brand context (tokens, visual identity)

The clarifier will determine:
- Which asset type(s) to generate
- Target platforms (web, iOS, Android)
- Size requirements
- Any customization or overrides

### Step 3: Start Preview Server

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/start-server.sh --project-dir <project-dir>
```

Save `screen_dir` and `state_dir`. Tell user to open the URL.

### Step 4: Generate Preview

Based on the clarified requirements, generate a preview of the assets.

**For icons/logos:**
- Create an SVG in the content directory
- Write an HTML preview showing the icon at different sizes and on different backgrounds
- Use `.logo-preview` and `.logo-preview.dark-bg` for light/dark previews

**For color palette:**
- Write an HTML page showing all brand colors as swatches
- Include WCAG contrast ratios between text and background colors
- Use `.swatches` + `.swatch` and `.token-grid` + `.token-item`

**For design tokens:**
- Show a preview of what each format will look like (CSS vars, SCSS, Tailwind)
- Use `.mockup` container with code-formatted previews

**For typography specimen:**
- Write an HTML page demonstrating the full type system
- Show heading levels, body text, captions at actual sizes
- Use `.type-specimen` classes

**For text content:**
- Generate taglines, microcopy, and tone examples
- Show in the browser with the brand's typography and colors applied

### Step 5: Iterate

Read `$STATE_DIR/events` for browser interactions. Combine with terminal feedback.

If the user wants changes:
- Modify the preview (write a new versioned HTML file)
- Repeat until approved

### Step 6: Export

Run the appropriate scripts to produce final assets:

**Icons / App icon sets:**
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/export-icons.sh <input.svg> <output-dir> --platforms web,ios,android
```
This produces:
- `web/` — favicon-16x16, favicon-32x32, apple-touch-icon-180x180, icon-192, icon-512, icon.svg
- `ios/AppIcon.appiconset/` — all required sizes + Contents.json
- `android/mipmap-*/` — mdpi through xxxhdpi

**Design tokens:**
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/generate-tokens.sh <tokens.json> <output-dir> --formats json,css,scss,tailwind
```
This produces: `tokens.json`, `tokens.css`, `_tokens.scss`, `tailwind.tokens.js`

**Logos:** Write SVG files directly using the Write tool.

**Color palette / Typography specimen / Text content:** Write as standalone HTML files and/or markdown documents.

Present the user with a list of all exported files and their locations.

### Step 7: Clean Up

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/stop-server.sh <session-dir>
```

## Key Principles

- **Read before generating** — always understand the existing brand first
- **Preview before export** — show the user what they'll get
- **Scripts for deterministic work** — use export-icons.sh and generate-tokens.sh for reliable output
- **Respect the brand** — generated assets must be consistent with the established identity
- **One asset type at a time** — clarify scope, generate, get approval, move to next if needed
