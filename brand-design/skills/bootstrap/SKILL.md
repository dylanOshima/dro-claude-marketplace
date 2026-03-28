---
name: bootstrap
description: This skill should be used when the user asks to "create a brand", "bootstrap a brand", "define a design system", "build a visual identity", "start brand design", "brandy bootstrap", or invokes /brandy:bootstrap. Orchestrates the full brand creation workflow — from understanding to strategy to visual identity to design system export.
---

# Brandy Bootstrap

Create a complete brand identity and design system through an interactive, phased workflow.

## Overview

Bootstrap orchestrates 6 specialized agents in sequence, with a visual companion (browser-based preview) for interactive feedback. Each agent asks the user questions and shows work in the browser before passing to the next phase.

## Checklist

Complete these steps in order:

1. **Detect context** — determine if bootstrapping from scratch or from an existing codebase
2. **Run clarifier** — extract structured understanding of the product and brand
3. **Start preview server** — launch the visual companion for interactive feedback
4. **Run brand strategist** — define positioning, personality, values, messaging
5. **Run creative director** — translate strategy into 2-3 visual directions, user selects
6. **Run designer** — apply visual identity to product UI mockups
7. **Run design system architect** — convert designs into scalable token/component system
8. **Run integrator** — produce final deliverables and write to output directory
9. **Stop preview server** — clean up

## Process

### Step 1: Detect Context

Check if the user provided a path to an existing codebase or project directory.

If a codebase exists, run the analysis script:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/analyze-codebase.sh <project-dir>
```

This detects: CSS variables, Tailwind config, design token files, UI frameworks (MUI, Chakra, etc.), component directories, brand assets (logos, icons, fonts), and iOS xcassets.

Pass the analysis results to the clarifier as context.

If no codebase exists, proceed with a blank slate.

### Step 2: Run Clarifier Agent

Dispatch the `brandy-clarifier` agent with:
- The user's initial input
- Any codebase analysis results
- Mode: `bootstrap`

The clarifier will ask the user targeted questions (max 3 rounds) and produce a structured context summary covering: product purpose, audience, platforms, personality, and constraints.

### Step 3: Start Preview Server

Launch the visual companion:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/start-server.sh --project-dir <project-dir>
```

Save `screen_dir` and `state_dir` from the JSON response. Tell the user to open the URL in their browser.

**Server management:**
- Before each write, verify `$STATE_DIR/server-info` exists. If missing, restart.
- Use semantic filenames: `strategy.html`, `visual-directions.html`, `mockups.html`
- Never reuse filenames — use versioning like `visual-directions-v2.html`
- After writing HTML, tell the user what's on screen and remind them of the URL
- Read `$STATE_DIR/events` after each user response to capture browser interactions

### Step 4: Run Brand Strategist

Dispatch the `brandy-strategist` agent with the clarified context.

The strategist will:
- Propose brand positioning, personality traits, archetype, tone of voice
- Ask the user refining questions
- Present the full brand strategy for approval

No browser content needed for this phase unless the strategist wants to show tone examples.

### Step 5: Run Creative Director

Dispatch the `brandy-creative-director` agent with the approved brand strategy.

The creative director will:
- Ask about visual preferences and constraints
- Develop 2-3 creative directions
- Write HTML to `screen_dir` showing color palettes, typography specimens, and mockup elements
- User selects and refines a direction in the browser

Use the frame template's CSS classes for rich previews:
- `.swatches` + `.swatch` for color palettes
- `.type-specimen` for typography samples
- `.cards` + `.card` for side-by-side comparison
- `.options` + `.option` for A/B/C selection

### Step 6: Run Designer

Dispatch the `brandy-designer` agent with the approved visual identity.

The designer will:
- Ask about key screens and flows
- Create HTML mockups showing the brand applied to realistic product UI
- Present in the browser for feedback
- Iterate on specific screens

### Step 7: Run Design System Architect

Dispatch the `brandy-architect` agent with the approved designs.

The architect will:
- Extract design tokens from the visual system
- Ask about implementation preferences (frameworks, token formats)
- Show token previews in the browser (color grid, spacing scale, type scale)
- Define component specifications

### Step 8: Run Integrator

Dispatch the `brandy-integrator` agent to produce final deliverables.

Determine output directory — default is `brand/` at the project root, or user-specified path.

The integrator writes:
- `brand-guide.md` — brand documentation
- `design-system.md` — design system specification
- `tokens/` — design tokens via `${CLAUDE_PLUGIN_ROOT}/scripts/generate-tokens.sh`
- `assets/` — SVG logo variants
- `README.md` — quick reference

Show a final summary in the browser.

### Step 9: Clean Up

Stop the preview server:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/stop-server.sh <session-dir>
```

Present the user with a summary of all files created and next steps.

## Visual Companion Reference

The preview server watches `screen_dir` for HTML files and serves the newest one. Write content fragments (no `<!DOCTYPE>` or `<html>` wrapper) — the server wraps them in the frame template automatically.

**Available CSS classes:** `.options`, `.option`, `.cards`, `.card`, `.mockup`, `.split`, `.pros-cons`, `.swatches`, `.swatch`, `.type-specimen`, `.logo-preview`, `.token-grid`, `.token-item`, `.placeholder`, `.mock-nav`, `.mock-button`, `.mock-input`

**User interactions** are recorded to `$STATE_DIR/events` as JSON lines. Read this file after each user response.

**Waiting screen:** When returning to terminal-only questions, push a waiting screen:
```html
<div style="display:flex;align-items:center;justify-content:center;min-height:60vh">
  <p class="subtitle">Continuing in terminal...</p>
</div>
```

## Key Principles

- **Collaborative journey** — every agent asks questions, the user stays in the loop
- **Show, don't tell** — use the browser for anything visual
- **Sequential, not parallel** — each phase builds on the previous
- **Opinionated defaults** — make strong recommendations, let user override
- **Production-ready output** — deliverables should be directly usable by developers
