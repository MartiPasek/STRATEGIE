# Publishing to VS Code Marketplace

Step-by-step guide to publish Speak Claude to the VS Code Marketplace.

## Prerequisites

1. **GitHub Account** - Create repo for speak-claude
2. **Azure DevOps Account** - Needed for publisher credentials
3. **Microsoft Account** - To sign in to Azure DevOps

## Step 1: Create GitHub Repository

```bash
cd speak-claude
git init
git add .
git commit -m "Initial commit: Speak Claude v1.0.0"
git branch -M main

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/speak-claude.git
git push -u origin main
```

## Step 2: Update Repository URLs

Edit `vscode-voice-to-text/package.json` and replace `YOUR_USERNAME`:

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/YOUR_ACTUAL_USERNAME/speak-claude"
  },
  "bugs": {
    "url": "https://github.com/YOUR_ACTUAL_USERNAME/speak-claude/issues"
  },
  "homepage": "https://github.com/YOUR_ACTUAL_USERNAME/speak-claude#readme"
}
```

## Step 3: Create Publisher Account

1. Go to https://marketplace.visualstudio.com/manage
2. Sign in with Microsoft Account
3. Click **Create publisher**
4. Fill in:
   - **Publisher ID**: `your-publisher-id` (e.g., `sylvester`, `speakclaude`)
   - **Display Name**: Your name or project name
   - **Email**: Your contact email

## Step 4: Get Personal Access Token

1. Go to https://dev.azure.com
2. Click **User settings** (top right) → **Personal access tokens**
3. Click **+ New Token**
4. Name: `vsce-publish`
5. Organization: **All accessible organizations**
6. Expiration: **90 days** (or custom)
7. Scopes: **Full access** OR select **Marketplace (Manage)**
8. Click **Create**
9. **Copy the token** (you won't see it again!)

## Step 5: Update Extension Publisher

Edit `vscode-voice-to-text/package.json`:

```json
{
  "publisher": "your-actual-publisher-id"
}
```

Replace `meetingmind` with your actual publisher ID from Step 3.

## Step 6: Rebuild Extension

```bash
cd vscode-voice-to-text
npm run package
```

## Step 7: Login to VS Code Marketplace

```bash
npx vsce login your-publisher-id
```

When prompted, paste your Personal Access Token from Step 4.

## Step 8: Publish!

```bash
npx vsce publish
```

This will:
- ✅ Package your extension
- ✅ Upload to VS Code Marketplace
- ✅ Make it available worldwide!

## Step 9: Verify Publication

1. Go to https://marketplace.visualstudio.com/
2. Search for "Speak Claude" or "Voice to Text WhisperX"
3. Your extension should appear!

## Updating the Extension

When you make changes:

1. **Update version** in `package.json`:
   ```json
   {
     "version": "1.0.1"  // Increment version
   }
   ```

2. **Commit changes**:
   ```bash
   git add .
   git commit -m "Version 1.0.1: Bug fixes and improvements"
   git push
   ```

3. **Publish update**:
   ```bash
   cd vscode-voice-to-text
   npm run package
   npx vsce publish
   ```

## Versioning Guide

Follow [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Patch** (1.0.0 → 1.0.1): Bug fixes

Examples:
- `1.0.1` - Fixed WhisperX connection error
- `1.1.0` - Added support for Spanish language
- `2.0.0` - Changed keybinding, breaking change

## Marketplace Best Practices

### 1. Good README

- ✅ Add screenshots/GIFs
- ✅ Clear installation instructions
- ✅ Troubleshooting section
- ✅ Examples

### 2. Keywords

Already included in `package.json`:
- voice, speech-to-text, whisperx, claude, ai, transcription

### 3. Categories

Consider changing from "Other" to:
```json
{
  "categories": ["Other", "Machine Learning", "Productivity"]
}
```

### 4. Changelog

Create `CHANGELOG.md`:

```markdown
# Changelog

## [1.0.0] - 2026-01-25

### Added
- Initial release
- Voice recording with Cmd+Shift+C
- WhisperX transcription
- Claude Code integration
- Local privacy-first architecture
```

## Troubleshooting

### "Publisher not found"

Run `npx vsce login your-publisher-id` again.

### "PAT expired"

Create new token in Azure DevOps (Step 4).

### "Repository field is missing"

Update `package.json` with GitHub URL (Step 2).

### "Icon too large"

Extension icons should be ≤ 128x128 PNG. Ours is 192x192 but VS Code will resize.

## Unpublishing

**⚠️ Be careful!** Unpublishing removes it for all users.

```bash
npx vsce unpublish your-publisher-id.voice-to-text
```

## Analytics

View stats at: https://marketplace.visualstudio.com/manage/publishers/your-publisher-id

Track:
- Downloads
- Ratings
- Reviews
- Trend over time

---

## Quick Reference

```bash
# Login
npx vsce login your-publisher-id

# Publish
npx vsce publish

# Publish specific version
npx vsce publish 1.0.1

# Publish patch/minor/major
npx vsce publish patch  # 1.0.0 → 1.0.1
npx vsce publish minor  # 1.0.0 → 1.1.0
npx vsce publish major  # 1.0.0 → 2.0.0

# Package without publishing
npx vsce package

# Show what will be packaged
npx vsce ls
```

---

**Congratulations!** Your extension is now live on the VS Code Marketplace! 🎉

Share it on:
- Twitter/X
- Reddit (/r/vscode, /r/ChatGPT, /r/ClaudeAI)
- Hacker News
- Product Hunt
- LinkedIn
