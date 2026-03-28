#!/usr/bin/env bash
# Analyze an existing codebase for design system artifacts
# Usage: analyze-codebase.sh <project-dir>
#
# Scans for: CSS variables, Tailwind config, design tokens, UI frameworks,
# component libraries, brand assets, and iOS xcassets.
#
# Outputs JSON summary of discovered design system elements.

set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "{\"error\": \"Directory not found: $PROJECT_DIR\"}"
  exit 1
fi

BRANDY_PROJECT_DIR="$PROJECT_DIR" node -e "
const fs = require('fs');
const path = require('path');

const projectDir = process.env.BRANDY_PROJECT_DIR;
const result = {
  css_variables: [],
  tailwind_config: null,
  token_files: [],
  ui_framework: null,
  component_dirs: [],
  brand_assets: [],
  xcassets: [],
  fonts: []
};

// Recursive file finder
function walk(dir, maxDepth = 5, depth = 0) {
  if (depth > maxDepth) return [];
  const files = [];
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === '.git' || entry.name === 'dist' || entry.name === 'build') continue;
      if (entry.isDirectory()) {
        files.push(...walk(fullPath, maxDepth, depth + 1));
      } else {
        files.push(fullPath);
      }
    }
  } catch (e) {}
  return files;
}

const allFiles = walk(projectDir);
const relPath = (p) => path.relative(projectDir, p);

// 1. CSS/SCSS files with custom properties
for (const f of allFiles) {
  if (/\.(css|scss|sass|less)$/.test(f)) {
    try {
      const content = fs.readFileSync(f, 'utf-8');
      const vars = content.match(/--[\\w-]+\\s*:/g);
      if (vars && vars.length > 0) {
        result.css_variables.push({
          file: relPath(f),
          count: vars.length,
          sample: vars.slice(0, 5).map(v => v.replace(':', '').trim())
        });
      }
    } catch (e) {}
  }
}

// 2. Tailwind config
for (const f of allFiles) {
  const name = path.basename(f);
  if (/^tailwind\\.config\\.(js|ts|cjs|mjs)$/.test(name)) {
    result.tailwind_config = relPath(f);
    break;
  }
}

// 3. Token/theme files
for (const f of allFiles) {
  const name = path.basename(f).toLowerCase();
  if (/^(tokens?|theme|design[-_]?tokens?)\\.(json|js|ts|yaml|yml)$/.test(name)) {
    result.token_files.push(relPath(f));
  }
}

// 4. UI framework detection via package.json
const pkgPath = path.join(projectDir, 'package.json');
if (fs.existsSync(pkgPath)) {
  try {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    const allDeps = { ...pkg.dependencies, ...pkg.devDependencies };
    const frameworks = {
      '@mui/material': 'Material UI',
      '@chakra-ui/react': 'Chakra UI',
      'antd': 'Ant Design',
      '@mantine/core': 'Mantine',
      'tailwindcss': 'Tailwind CSS',
      '@radix-ui/react-dialog': 'Radix UI',
      'styled-components': 'styled-components',
      '@emotion/react': 'Emotion',
      'react-native': 'React Native',
      '@expo/vector-icons': 'Expo',
      'nativewind': 'NativeWind'
    };
    const detected = [];
    for (const [dep, name] of Object.entries(frameworks)) {
      if (allDeps[dep]) detected.push(name);
    }
    if (detected.length > 0) result.ui_framework = detected;
  } catch (e) {}
}

// 5. Component directories
const componentPatterns = ['components', 'ui', 'design-system', 'ds', 'atoms', 'molecules', 'organisms'];
for (const f of allFiles) {
  const dir = path.dirname(f);
  const dirName = path.basename(dir).toLowerCase();
  if (componentPatterns.includes(dirName) && !result.component_dirs.includes(relPath(dir))) {
    result.component_dirs.push(relPath(dir));
  }
}

// 6. Brand assets
for (const f of allFiles) {
  if (/\\.(svg|png|jpg|jpeg|ico|webp)$/i.test(f)) {
    const name = path.basename(f).toLowerCase();
    if (/logo|brand|icon|favicon|mark/.test(name)) {
      result.brand_assets.push(relPath(f));
    }
  }
}

// 7. iOS xcassets
for (const f of allFiles) {
  if (f.endsWith('.xcassets') || path.dirname(f).includes('.xcassets')) {
    const xcDir = f.includes('.xcassets/') ? f.split('.xcassets/')[0] + '.xcassets' : f;
    const rel = relPath(xcDir);
    if (!result.xcassets.includes(rel)) {
      result.xcassets.push(rel);
    }
  }
}

// 8. Font files
for (const f of allFiles) {
  if (/\\.(woff2?|ttf|otf|eot)$/i.test(f)) {
    result.fonts.push(relPath(f));
  }
}

// Deduplicate
result.component_dirs = [...new Set(result.component_dirs)].slice(0, 10);
result.brand_assets = result.brand_assets.slice(0, 20);
result.xcassets = [...new Set(result.xcassets)];
result.fonts = result.fonts.slice(0, 20);

console.log(JSON.stringify(result, null, 2));
"
