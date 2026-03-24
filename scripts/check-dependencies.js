#!/usr/bin/env node

/**
 * Script to check for outdated dependencies across all plugins
 */

const fs = require('fs');
const path = require('path');

const PACKAGES_DIR = path.join(__dirname, '..', 'packages');

function getPluginDirs() {
  return fs.readdirSync(PACKAGES_DIR, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);
}

function parseRequirements(content) {
  return content.split('\n')
    .filter(line => line.trim() && !line.startsWith('#'))
    .map(line => {
      const match = line.match(/^([a-zA-Z0-9_-]+)([>=<~!]+.*)?$/);
      if (match) {
        return { name: match[1], constraint: match[2] || '' };
      }
      return null;
    })
    .filter(Boolean);
}

function checkPlugin(pluginDir) {
  const reqPath = path.join(PACKAGES_DIR, pluginDir, 'requirements.txt');

  if (!fs.existsSync(reqPath)) {
    console.log(`\n📦 ${pluginDir}: No dependencies`);
    return;
  }

  const content = fs.readFileSync(reqPath, 'utf8');
  const deps = parseRequirements(content);

  if (deps.length === 0) {
    console.log(`\n📦 ${pluginDir}: No dependencies`);
    return;
  }

  console.log(`\n📦 ${pluginDir}:`);
  deps.forEach(dep => {
    console.log(`  - ${dep.name}${dep.constraint ? ` (${dep.constraint})` : ''}`);
  });
}

async function main() {
  console.log('🔍 Checking dependencies across all plugins...\n');

  const plugins = getPluginDirs();

  for (const plugin of plugins) {
    checkPlugin(plugin);
  }

  console.log('\n✅ Dependency check complete!');
}

main().catch(console.error);
