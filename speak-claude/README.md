<div align="center">
  <img src="logo.png" alt="Speak Claude Logo" width="200"/>

  # Speak Claude 🎤

  **Voice-to-text extension for VS Code that lets you talk to Claude Code instead of typing.**

  Uses WhisperX running locally for fast, accurate transcription.

  [![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blue)](https://marketplace.visualstudio.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
</div>

## Features

- 🎙️ **Press `Cmd+Shift+C` to record** - Start/stop with a keyboard shortcut
- 🤖 **Local WhisperX transcription** - Privacy-first, no cloud APIs needed
- 💬 **Works everywhere** - Claude Code, text editors, terminal, any input field
- ⚡ **Fast & accurate** - High-quality speech recognition with English support
- 🔊 **Visual feedback** - Status bar shows recording state

## Demo

1. Press `Cmd+Shift+C` (Mac) or `Ctrl+Shift+C` (Windows/Linux)
2. Speak your prompt: "Help me refactor this function"
3. Press `Cmd+Shift+C` again to stop
4. Text appears at your cursor!

## Prerequisites

### 1. SoX (Audio Recording)

**macOS:**
```bash
brew install sox
```

**Ubuntu/Debian:**
```bash
sudo apt-get install sox libsox-fmt-all
```

**Windows:**
Download from [SoX SourceForge](https://sourceforge.net/projects/sox/files/sox/)

### 2. Docker (Recommended) OR Python 3.11+

**Option A: Docker** (Easiest)
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- One command setup: `docker-compose up -d`

**Option B: Python**
- Python 3.11+ required for manual setup

## Quick Start

### Step 1: Start WhisperX Service

**🐳 Docker (Recommended):**
```bash
cd speak-claude
docker-compose up -d

# Verify it's running
curl http://localhost:48001/health
```

**🐍 Python (Manual):**
```bash
cd speak-claude/whisperx-service
pip install -r requirements.txt
pip install whisperx
uvicorn main:app --host 0.0.0.0 --port 48001
```

Service available at `http://localhost:48001`.

### Step 2: Install VS Code Extension

```bash
cd speak-claude/vscode-voice-to-text
npm install
npm run compile
npm run package
```

Then in VS Code:
1. Press `Cmd+Shift+P`
2. Type "Extensions: Install from VSIX"
3. Select `vscode-voice-to-text/voice-to-text-1.0.0.vsix`
4. Reload VS Code

### Step 3: Configure (Optional)

Create `.vscode/settings.json` in your workspace:

```json
{
  "voiceToText.language": "en",
  "voiceToText.whisperxUrl": "http://localhost:48001",
  "voiceToText.diarization": false
}
```

### Step 4: Use It!

1. Open Claude Code or any text editor
2. Press `Cmd+Shift+C`
3. Speak clearly
4. Press `Cmd+Shift+C` to stop
5. Text appears at cursor position

## How It Works

```
┌─────────────────┐
│   Press hotkey  │
│   Cmd+Shift+C   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SoX records   │
│   microphone    │
│   to WAV file   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Send audio    │
│   to WhisperX   │
│   (localhost)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   WhisperX AI   │
│   transcribes   │
│   to text       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Insert text   │
│   at cursor     │
└─────────────────┘
```

## Configuration

### VS Code Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `voiceToText.whisperxUrl` | `http://localhost:48001` | WhisperX service URL |
| `voiceToText.language` | `""` (auto-detect) | Language code (`en`, `es`, etc.) |
| `voiceToText.diarization` | `false` | Enable speaker labels (requires HF_TOKEN) |

### WhisperX Model Size (Docker)

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` to change model:
```env
WHISPERX_MODEL=small  # Options: tiny, base, small, medium, large-v2
```

Restart: `docker-compose restart`

**Model Comparison:**
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39M | Fastest | Good |
| base | 74M | Fast | Better |
| small | 244M | Medium | Very Good |
| medium | 769M | Slow | Excellent |

### Docker Commands

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f whisperx

# Stop service
docker-compose down

# Restart after config changes
docker-compose restart
```

## Project Structure

```
speak-claude/
├── vscode-voice-to-text/       # VS Code extension
│   ├── src/
│   │   └── extension.ts        # Main extension code
│   ├── package.json
│   └── README.md
├── whisperx-service/           # WhisperX transcription service
│   ├── main.py                 # FastAPI service
│   ├── requirements.txt
│   └── Dockerfile
└── README.md                   # This file
```

## Use Cases

### 1. Talk to Claude Code
Dictate prompts to Claude Code instead of typing.

### 2. Voice Comments
Add code comments by speaking.

### 3. Terminal Commands
Dictate complex bash commands.

### 4. Documentation
Write README files and docs with your voice.

## Troubleshooting

### "sox not found"
Install SoX (see Prerequisites).

### "WhisperX service is not running"
Start the service:
```bash
cd whisperx-service
uvicorn main:app --port 48001
```

### "Transcription failed: 400 Bad Request"
Check that:
1. WhisperX service is running
2. Audio file has content (speak after pressing record)
3. Language setting is correct

### "No speech detected"
- Speak closer to microphone
- Check system microphone permissions
- Ensure microphone is not muted
- Speak for at least 1-2 seconds

### Wrong language detected
Set language explicitly in settings:
```json
{
  "voiceToText.language": "en"
}
```

## Development

### Build Extension
```bash
cd vscode-voice-to-text
npm install
npm run compile
```

### Test in Dev Mode
1. Open `vscode-voice-to-text` in VS Code
2. Press `F5` to launch Extension Development Host
3. Test the extension in the new window

### Package Extension
```bash
npm run package
# Creates: voice-to-text-1.0.0.vsix
```

## Tech Stack

- **Extension**: TypeScript, VS Code Extension API
- **Recording**: SoX (Sound eXchange)
- **Transcription**: WhisperX (faster-whisper + alignment)
- **Backend**: FastAPI, Python
- **Audio**: 16kHz WAV, mono, 16-bit

## Keyboard Shortcuts

| Command | Mac | Windows/Linux |
|---------|-----|---------------|
| Record/Stop | `Cmd+Shift+C` | `Ctrl+Shift+C` |

## Privacy

All transcription happens **locally on your machine**. No audio is sent to external APIs or cloud services. Your voice data stays private.

## Performance

- **Recording**: Instant (SoX)
- **Transcription**: ~1-2 seconds for short clips (depends on CPU)
- **Model**: WhisperX "base" (39M params, 1GB RAM)

For faster transcription, upgrade to a GPU or use the "tiny" model.

## Roadmap

- [ ] Push-to-talk mode (hold key to record)
- [ ] Custom wake word ("Hey Claude...")
- [ ] Automatic punctuation
- [ ] Multi-language support UI
- [ ] Cursor extension support
- [ ] JetBrains IDE support

## Contributing

Contributions welcome! Open issues or PRs on GitHub.

## License

MIT

## Credits

- Built for [Claude Code](https://claude.com/claude-code)
- Uses [WhisperX](https://github.com/m-bain/whisperX) for transcription
- Inspired by voice coding workflows

---

**Made with 🎤 by Sylvester**

*Talk to your code, don't type it.*
