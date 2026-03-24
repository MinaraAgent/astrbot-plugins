#!/usr/bin/env node

/**
 * Release script for publishing plugins
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PACKAGES_DIR = path.join(__dirname, '..', 'packages');

function getPluginDirs() {
  return fs.readdirSync(PACKAGES_DIR, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);
}

function getPluginVersion(pluginDir) {
  const metadataPath = path.join(PACKAGES_DIR, pluginDir, 'metadata.yaml');
  if (fs.existsSync(metadataPath)) {
    const content = fs.readFileSync(metadataPath, 'utf8');
    const match = content.match(/version:\s*"([^"]+)"/);
    return match ? match[1] : null;
  }
  return null;
}

function createRelease(pluginDir, version) {
  console.log(`\n🚀 Releasing ${pluginDir} v${version}`);

  try {
    // Create tag
    const tag = `${pluginDir}-v${version}`;
    execSync(`git tag -a ${tag} -m "Release ${pluginDir} version ${version}"`, { stdio: 'inherit' });

    console.log(`  ✅ Created tag: ${tag}`);
  } catch (error) {
    console.error(`  ❌ Failed to create release for ${pluginDir}`, error.message);
  }
}

async function main() {
  const plugins = getPluginDirs();

  console.log('📋 Preparing release for plugins...\n');

  for (const plugin of plugins) {
    const version = getPluginVersion(plugin);
    if (version) {
      createRelease(plugin, version);
    }
  }

  console.log('\n✅ Release preparation complete!');
  console.log('\n📝 To push tags to remote, run:');
  console.log('  git push --tags');
}

main().catch(console.error);
