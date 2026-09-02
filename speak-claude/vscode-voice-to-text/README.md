# Speak Claude - Voice to Text for VS Code

🎤 Voice-to-text extension for VS Code and Claude Code using local WhisperX transcription. Privacy-first, runs entirely on your machine!

> **Want to skip the local setup?** Try [**Speak Claw**](https://marketplace.visualstudio.com/items?itemName=slycreator.speakclaw) — our cloud-powered version. No Docker, no WhisperX, no local transcription service. Just install, add your API token, and start speaking. [Get Speak Claw →](https://speakclaw.com)

**Quick Start (self-hosted):**
1. Install this extension from VS Code Marketplace
2. Clone the repo: `git clone https://github.com/SlyCreator/speak-claude.git`
3. Run WhisperX: `cd speak-claude && docker-compose up -d`
4. Press `Cmd+Shift+C` anywhere in VS Code to dictate!

## Features

- 🎤 **Voice Recording**: Press `Cmd+Shift+C` (Mac) or `Ctrl+Shift+C` (Windows/Linux) to start/stop recording
- 🤖 **WhisperX Integration**: Uses your local WhisperX service for high-quality transcription
- 💬 **Works Everywhere**: Inserts text into any VS Code editor, terminal, or input field (including Claude Code chat)
- ⚙️ **Configurable**: Set WhisperX URL, language, and diarization options

## Prerequisites

> ⚠️ **IMPORTANT**: This extension requires the WhisperX service to be running locally. You must clone the repository and set up WhisperX before using this extension.

### 1. Clone the Repository

First, clone the Speak Claude repository to get the WhisperX service:

```bash
git clone https://github.com/SlyCreator/speak-claude.git
cd speak-claude
```

### 2. Set Up WhisperX Service

**Option A: Docker (Recommended)**

```bash
docker-compose up -d
```

The service will start at `http://localhost:48001`

**Option B: Manual Python Setup**

```bash
cd whisperx-service
pip install -r requirements.txt
pip install whisperx
uvicorn main:app --host 0.0.0.0 --port 48001
```

### 3. Install SoX (Sound eXchange)

The extension uses SoX for audio recording. Install it:

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

## Installation

### Install from VS Code Marketplace (Recommended)

1. Open VS Code
2. Go to Extensions (`Cmd+Shift+X` or `Ctrl+Shift+X`)
3. Search for "Speak Claude"
4. Click Install

Or install via command line:
```bash
code --install-extension slycreator.speak-claude
```

### After Installation

Make sure you have:
1. ✅ Cloned the repository (see Prerequisites above)
2. ✅ WhisperX service running at `http://localhost:48001`
3. ✅ SoX installed on your system

Then press `Cmd+Shift+C` to start using voice input!

## Usage

### Two Ways to Start Recording

**Option 1: Keyboard Shortcut (Recommended)**
- Press `Cmd+Shift+C` (Mac) or `Ctrl+Shift+C` (Windows/Linux)

**Option 2: Status Bar Button**
- Click the **"Speak Claude"** button in the status bar (bottom-right corner of VS Code)

![Status Bar Button](https://raw.githubusercontent.com/SlyCreator/speak-claude/main/vscode-voice-to-text/status-bar.png)

### Basic Usage

1. **Start Recording**: Use keyboard shortcut or click status bar button
   - Status bar will show "🎤 Recording..."

2. **Speak**: Say what you want to transcribe

3. **Stop Recording**: Press the shortcut again or click the status bar button
   - Extension sends audio to WhisperX
   - Transcribed text appears at cursor position

### Using with Claude Code

1. Open Claude Code chat (`Esc` to focus input)
2. Start recording (keyboard or status bar button)
3. Speak your prompt
4. Stop recording
5. Text appears in Claude Code input

## Configuration

Open VS Code settings (`Cmd+,`) and search for "Voice to Text":

- **WhisperX URL**: Default is `http://localhost:48001`
- **Language**: Language code (e.g., `en`, `es`). Leave empty for auto-detection.
- **Diarization**: Enable speaker labels (requires HF_TOKEN in WhisperX service)

Or edit `.vscode/settings.json`:

```json
{
  "voiceToText.whisperxUrl": "http://localhost:48001",
  "voiceToText.language": "en",
  "voiceToText.diarization": false
}
```

## Troubleshooting

### "sox not found"

Install SoX (see Prerequisites above).

### "WhisperX service is not running"

Start the WhisperX service:
```bash
cd whisperx-service
uvicorn main:app --port 48001
```

### "No speech detected"

- Speak closer to the microphone
- Check system microphone permissions
- Ensure microphone is not muted

### "Transcription failed: timeout"

The audio file might be too long. Try shorter recordings (under 30 seconds).

## How It Works

1. **Recording**: Uses SoX to capture audio from your default microphone
2. **File**: Saves as 16kHz mono WAV file (optimized for speech)
3. **Upload**: Sends to WhisperX `/transcribe` endpoint
4. **Response**: Gets transcript text
5. **Insertion**: Inserts text at cursor position or copies to clipboard

## Keyboard Shortcuts

| Command | Mac | Windows/Linux |
|---------|-----|---------------|
| Start/Stop Recording | `Cmd+Shift+C` | `Ctrl+Shift+C` |

## Commands

Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`):

- **Voice to Text: Start Recording** - Start/stop voice recording

## Requirements

- VS Code 1.85.0 or higher
- Node.js (for development)
- SoX (for audio recording)
- WhisperX service running on localhost:48001

## License

MIT

## Credits

Built for the MeetingMind AI project. Uses [WhisperX](https://github.com/m-bain/whisperX) for transcription.
