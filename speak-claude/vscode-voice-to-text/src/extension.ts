import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';
import FormData from 'form-data';

let recordingProcess: ChildProcess | null = null;
let recordingFile: string | null = null;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
    console.log('Voice to Text extension activated');

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'voice-to-text.record';
    statusBarItem.text = '$(unmute) Speak Claude';
    statusBarItem.tooltip = 'Click to start voice recording (Cmd+Shift+C)';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Register command
    let disposable = vscode.commands.registerCommand('voice-to-text.record', async () => {
        if (recordingProcess) {
            // Already recording, stop it
            await stopRecording();
        } else {
            // Start recording
            await startRecording();
        }
    });

    context.subscriptions.push(disposable);
}

async function startRecording() {
    try {
        // Check if sox is installed
        const soxCheck = spawn('which', ['sox']);
        await new Promise<void>((resolve, reject) => {
            soxCheck.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error('sox not found'));
                } else {
                    resolve();
                }
            });
        });

        // Create temporary file for recording
        recordingFile = path.join(os.tmpdir(), `voice-${Date.now()}.wav`);

        // Start recording with sox
        recordingProcess = spawn('sox', [
            '-d',           // Default audio device
            '-r', '16000',  // Sample rate 16kHz (good for speech)
            '-c', '1',      // Mono
            '-b', '16',     // 16-bit
            recordingFile
        ]);

        // Update status bar
        statusBarItem.text = '$(mic) Recording...';
        statusBarItem.tooltip = 'Click to stop recording (Cmd+Shift+C)';
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');

        vscode.window.showInformationMessage('🎤 Recording... Press Cmd+Shift+C again to stop');

        recordingProcess.on('error', (err) => {
            vscode.window.showErrorMessage(`Recording failed: ${err.message}`);
            resetRecordingState();
        });

    } catch (error: any) {
        if (error.message === 'sox not found') {
            const answer = await vscode.window.showErrorMessage(
                'SoX is required for audio recording. Install it to use voice input.',
                'Install via Homebrew',
                'Cancel'
            );
            if (answer === 'Install via Homebrew') {
                vscode.env.openExternal(vscode.Uri.parse('https://formulae.brew.sh/formula/sox'));
            }
        } else {
            vscode.window.showErrorMessage(`Failed to start recording: ${error.message}`);
        }
        resetRecordingState();
    }
}

async function stopRecording() {
    if (!recordingProcess || !recordingFile) {
        return;
    }

    // Stop recording
    recordingProcess.kill('SIGINT');
    recordingProcess = null;

    // Update status bar to show processing
    statusBarItem.text = '$(loading~spin) Transcribing...';
    statusBarItem.tooltip = 'Processing audio...';

    try {
        // Wait a bit for file to be written
        await new Promise(resolve => setTimeout(resolve, 500));

        // Check if file exists and has content
        if (!fs.existsSync(recordingFile) || fs.statSync(recordingFile).size === 0) {
            throw new Error('No audio was recorded');
        }

        // Send to WhisperX service
        const config = vscode.workspace.getConfiguration('voiceToText');
        const whisperxUrl = config.get<string>('whisperxUrl', 'http://localhost:48001');
        const language = config.get<string>('language', '');
        const diarization = config.get<boolean>('diarization', false);

        const formData = new FormData();
        formData.append('file', fs.createReadStream(recordingFile), {
            filename: 'recording.wav',
            contentType: 'audio/wav'
        });
        formData.append('diarize', String(diarization));
        formData.append('align', 'true');
        if (language) {
            formData.append('language', language);
        }

        const response = await axios.post(`${whisperxUrl}/transcribe`, formData, {
            headers: formData.getHeaders(),
            timeout: 60000, // 60 second timeout
        });

        const transcript = response.data.transcript;

        if (!transcript || transcript.trim().length === 0) {
            throw new Error('No speech detected in recording');
        }

        // Insert text into active editor or input
        await insertText(transcript.trim());

        vscode.window.showInformationMessage(`✅ Transcribed: "${transcript.substring(0, 50)}${transcript.length > 50 ? '...' : ''}"`);

    } catch (error: any) {
        if (error.code === 'ECONNREFUSED') {
            vscode.window.showErrorMessage(
                `WhisperX service is not running. Start it with: cd whisperx-service && uvicorn main:app --port 48001`
            );
        } else {
            vscode.window.showErrorMessage(`Transcription failed: ${error.message}`);
        }
    } finally {
        // Cleanup
        if (recordingFile && fs.existsSync(recordingFile)) {
            fs.unlinkSync(recordingFile);
        }
        resetRecordingState();
    }
}

async function insertText(text: string) {
    // Try to insert into active text editor
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        await editor.edit(editBuilder => {
            editBuilder.insert(editor.selection.active, text);
        });
        return;
    }

    // If no editor, copy to clipboard and notify user
    await vscode.env.clipboard.writeText(text);
    vscode.window.showInformationMessage('Text copied to clipboard (no active editor found)');
}

function resetRecordingState() {
    recordingProcess = null;
    recordingFile = null;
    statusBarItem.text = '$(unmute) Speak Claude';
    statusBarItem.tooltip = 'Click to start voice recording (Cmd+Shift+C)';
    statusBarItem.backgroundColor = undefined;
}

export function deactivate() {
    if (recordingProcess) {
        recordingProcess.kill();
    }
    if (recordingFile && fs.existsSync(recordingFile)) {
        fs.unlinkSync(recordingFile);
    }
}
