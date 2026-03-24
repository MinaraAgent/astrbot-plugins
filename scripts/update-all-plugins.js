#!/usr/bin/env node

/**
 * Script to update all plugin metadata and version information
 */

const fs = require('fs');
const path = require('path');

const PACKAGES_DIR = path.join(__dirname, '..', 'packages');

function getPluginDirs() {
  return fs.readdirSync(PACKAGES_DIR, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);
}

function readMetadata(pluginDir) {
  const metadataPath = path.join(PACKAGES_DIR, pluginDir, 'metadata.yaml');
  if (fs.existsSync(metadataPath)) {
    return fs.readFileSync(metadataPath, 'utf8');
  }
  return null;
}

function updatePlugin(pluginDir) {
  console.log(`\n📦 Checking ${pluginDir}...`);

  const metadata = readMetadata(pluginDir);
  if (!metadata) {
    console.log(`  ⚠️  No metadata.yaml found`);
    return;
  }

  // Parse version from metadata
  const versionMatch = metadata.match(/version:\s*"([^"]+)"/);
  if (versionMatch) {
    console.log(`  ✅ Version: ${versionMatch[1]}`);
  }

  // Check for requirements.txt
  const reqPath = path.join(PACKAGES_DIR, pluginDir, 'requirements.txt');
  if (fs.existsSync(reqPath)) {
    console.log(`  📋 Dependencies: ${fs.readFileSync(reqPath, 'utf8').split('\n').filter(Boolean).length} packages`);
  }
}

async function main() {
  console.log('🔍 Checking all AstrBot plugins...\n');

  const plugins = getPluginDirs();

  if (plugins.length === 0) {
    console.log('❌ No plugin packages found');
    process.exit(1);
  }

  console.log(`Found ${plugins.length} plugins:`);

  for (const plugin of plugins) {
    updatePlugin(plugin);
  }

  console.log('\n✅ Update check complete!');
}

main().catch(console.error);
