---
name: stt-transcription
description: Speech-to-text transcription using multiple engines (Whisper, Google Speech, Azure, AssemblyAI). Record audio, transcribe files, real-time transcription, speaker diarization, timestamps, and multi-language support. Use for meeting transcription, voice notes, audio file processing, or accessibility features.
---

# Speech-to-Text Transcription

Comprehensive speech-to-text capabilities using multiple STT engines. Record audio, transcribe files, real-time processing, speaker identification, and multi-language support.

## Quick Start

When asked to transcribe audio:

1. **Choose engine**: Whisper (local/free), Google, Azure, or AssemblyAI
2. **Record or load**: Capture audio or use existing file
3. **Transcribe**: Convert speech to text
4. **Format**: Output as plain text, SRT, VTT, or JSON
5. **Enhance**: Add timestamps, speaker labels, punctuation

## Prerequisites

### System Requirements
- Python 3.8+
- Microphone (for recording)
- Audio file support: WAV, MP3, M4A, FLAC, OGG

### Install Dependencies

**Core (required):**
```bash
pip install sounddevice soundfile numpy --break-system-packages
```

**Whisper (OpenAI - local, free):**
```bash
pip install openai-whisper --break-system-packages
# For faster processing with GPU:
pip install openai-whisper torch --break-system-packages
```

**Google Speech (requires API key):**
```bash
pip install google-cloud-speech --break-system-packages
```

**Azure Speech (requires API key):**
```bash
pip install azure-cognitiveservices-speech --break-system-packages
```

**AssemblyAI (requires API key):**
```bash
pip install assemblyai --break-system-packages
```

**Optional enhancements:**
```bash
pip install pydub webrtcvad --break-system-packages  # Audio processing
pip install pyaudio --break-system-packages  # Alternative audio backend
```

See [reference/setup-guide.md](reference/setup-guide.md) for detailed installation.

## STT Engine Comparison

| Engine | Cost | Speed | Quality | Features | Best For |
|--------|------|-------|---------|----------|----------|
| **Whisper** | Free | Medium | High | Multilingual, local | Privacy, offline, free |
| **Google** | Pay-per-use | Fast | High | Punctuation, diarization | Real-time, accuracy |
| **Azure** | Pay-per-use | Fast | High | Translation, custom | Enterprise integration |
| **AssemblyAI** | Pay-per-use | Medium | Very High | Diarization, sentiment | Analysis, insights |

### Whisper (Recommended for most users)
- ✅ **Free and local** - No API costs, runs offline
- ✅ **High quality** - State-of-the-art accuracy
- ✅ **Multilingual** - 99+ languages
- ⚠️ **Speed** - Slower than cloud services (depends on hardware)
- ⚠️ **Resources** - Needs decent CPU/GPU

### Google Cloud Speech
- ✅ **Fast** - Real-time capable
- ✅ **Accurate** - Excellent for English
- ✅ **Features** - Automatic punctuation, speaker diarization
- ⚠️ **Cost** - $0.006 per 15 seconds (~$1.44/hour)
- ⚠️ **Privacy** - Audio sent to Google

### Azure Speech
- ✅ **Enterprise** - Microsoft integration
- ✅ **Translation** - Real-time translation
- ✅ **Custom** - Train custom models
- ⚠️ **Cost** - $1 per audio hour
- ⚠️ **Setup** - More complex configuration

## Azure Speech via Azure CLI (Recommended)

**Prefer using Azure CLI (`az`) over manual API key management.** This approach is more secure and integrates with existing Azure authentication.

### Prerequisites

1. **Install Azure CLI** and login:
   ```bash
   az login
   ```

2. **Install Azure Speech SDK:**
   ```bash
   pip install azure-cognitiveservices-speech
   ```

### Create Azure Speech Resource

```bash
# Create resource group (if not exists)
az group create --name stt-temp-rg --location eastasia -o table

# Create Speech resource (F0 = free tier, S0 = standard)
az cognitiveservices account create \
  --name stt-temp-speech \
  --resource-group stt-temp-rg \
  --kind SpeechServices \
  --sku F0 \
  --location eastasia \
  --yes -o table
```

### Get API Key and Transcribe

```bash
# Get API key
$key = (az cognitiveservices account keys list \
  --name stt-temp-speech \
  --resource-group stt-temp-rg \
  --query "key1" -o tsv)

# Set environment variables
$env:AZURE_SPEECH_KEY = $key
$env:AZURE_SPEECH_REGION = "eastasia"

# Run transcription (see Python code below)
```

### Azure Transcription Python Code

```python
import azure.cognitiveservices.speech as speechsdk
import os
import time

speech_key = os.environ['AZURE_SPEECH_KEY']
region = os.environ['AZURE_SPEECH_REGION']
audio_file = "path/to/audio.wav"  # Must be 16kHz mono PCM WAV
output_file = "transcript.txt"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
speech_config.speech_recognition_language = 'zh-CN'  # or 'en-US'

audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
speech_recognizer = speechsdk.SpeechRecognizer(
    speech_config=speech_config, 
    audio_config=audio_config
)

done = False
all_text = []

def recognized_cb(evt):
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        all_text.append(evt.result.text)
        print(f'[{len(all_text)}] {evt.result.text[:60]}...')

def stop_cb(evt):
    global done
    done = True

speech_recognizer.recognized.connect(recognized_cb)
speech_recognizer.session_stopped.connect(stop_cb)
speech_recognizer.canceled.connect(stop_cb)

speech_recognizer.start_continuous_recognition()
while not done:
    time.sleep(0.5)
speech_recognizer.stop_continuous_recognition()

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(all_text))
```

### Audio Format Requirements

Azure Speech requires specific audio format. Convert with ffmpeg:

```bash
ffmpeg -i "input.mp3" -acodec pcm_s16le -ar 16000 -ac 1 "output.wav" -y
```

### Resource Lock File (Multi-Agent Coordination)

⚠️ **CRITICAL:** When multiple agents may use Azure Speech concurrently, use a lock file to coordinate resource cleanup.

**Lock file location:** `locks/azure-stt-lock.json`

**Lock file format:**
```json
{
  "resource_group": "stt-temp-rg",
  "speech_resource": "stt-temp-speech",
  "active_sessions": [
    {
      "agent_id": "agent-123",
      "audio_file": "video1.wav",
      "started_at": "2026-02-01T10:00:00Z"
    },
    {
      "agent_id": "agent-456", 
      "audio_file": "video2.wav",
      "started_at": "2026-02-01T10:05:00Z"
    }
  ]
}
```

**Workflow with lock file:**

1. **Before starting transcription:**
   ```python
   # Read or create lock file
   # Add your session to active_sessions
   # If resource doesn't exist, create it
   ```

2. **After completing transcription:**
   ```python
   # Remove your session from active_sessions
   # If active_sessions is empty, delete Azure resources
   ```

3. **Cleanup logic:**
   ```bash
   # Only delete when no active sessions
   if (lock_file.active_sessions.length == 0):
       az group delete --name stt-temp-rg --yes --no-wait
       # Delete lock file
   ```

**Lock file operations (PowerShell):**

```powershell
# Read lock file
$lockFile = "locks/azure-stt-lock.json"
if (Test-Path $lockFile) {
    $lock = Get-Content $lockFile | ConvertFrom-Json
} else {
    $lock = @{
        resource_group = "stt-temp-rg"
        speech_resource = "stt-temp-speech"
        active_sessions = @()
    }
}

# Add session
$session = @{
    agent_id = [guid]::NewGuid().ToString()
    audio_file = "my-audio.wav"
    started_at = (Get-Date -Format "o")
}
$lock.active_sessions += $session
$lock | ConvertTo-Json -Depth 3 | Set-Content $lockFile

# Remove session and cleanup
$lock.active_sessions = $lock.active_sessions | Where-Object { $_.agent_id -ne $myAgentId }
if ($lock.active_sessions.Count -eq 0) {
    az group delete --name $lock.resource_group --yes --no-wait
    Remove-Item $lockFile
} else {
    $lock | ConvertTo-Json -Depth 3 | Set-Content $lockFile
}
```

### Cleanup Reminder

⚠️ **IMPORTANT:** After transcription is complete and no other agents are using the resource:

```bash
# Delete the entire resource group (removes all resources)
az group delete --name stt-temp-rg --yes

# Verify deletion
az group list --query "[?name=='stt-temp-rg']" -o table
```

**Never forget to:**
1. Check the lock file for other active sessions
2. Remove your session from the lock file
3. Delete Azure resources only when you are the last session
4. Delete the lock file after deleting resources

### AssemblyAI
- ✅ **Features** - Speaker diarization, sentiment analysis
- ✅ **Quality** - Very accurate
- ✅ **Developer-friendly** - Simple API
- ⚠️ **Cost** - $0.00025 per second (~$0.90/hour)

## Core Operations

### Record Audio

**Simple recording:**
```bash
# Record 30 seconds
python scripts/record_audio.py --duration 30 --output recording.wav

# Record until stopped (Ctrl+C)
python scripts/record_audio.py --output recording.wav

# Record with voice activity detection
python scripts/record_audio.py --vad --output recording.wav
```

**Advanced recording:**
```bash
# Choose microphone
python scripts/list_devices.py  # List available mics
python scripts/record_audio.py --device 1 --output recording.wav

# Specify quality
python scripts/record_audio.py \
  --sample-rate 48000 \
  --channels 2 \
  --output recording.wav
```

### Transcribe Files

**Using Whisper (local, free):**
```bash
# Basic transcription
python scripts/transcribe_whisper.py --file recording.wav

# Choose model size (tiny, base, small, medium, large)
python scripts/transcribe_whisper.py \
  --file recording.wav \
  --model medium

# With timestamps
python scripts/transcribe_whisper.py \
  --file recording.wav \
  --timestamps \
  --output transcript.json

# Multiple languages
python scripts/transcribe_whisper.py \
  --file recording.wav \
  --language es  # Spanish
```

**Using Google Cloud:**
```bash
# Export API key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# Transcribe
python scripts/transcribe_google.py \
  --file recording.wav \
  --language en-US

# With speaker diarization
python scripts/transcribe_google.py \
  --file recording.wav \
  --diarization \
  --speakers 2
```

**Using Azure:**
```bash
# Set credentials
export AZURE_SPEECH_KEY="your-key"
export AZURE_SPEECH_REGION="westus"

# Transcribe
python scripts/transcribe_azure.py --file recording.wav

# Real-time
python scripts/transcribe_azure_realtime.py --microphone
```

**Using AssemblyAI:**
```bash
# Set API key
export ASSEMBLYAI_API_KEY="your-key"

# Transcribe with features
python scripts/transcribe_assemblyai.py \
  --file recording.wav \
  --diarization \
  --sentiment \
  --topics
```

### Real-Time Transcription

**Stream from microphone:**
```bash
# Whisper streaming (chunked)
python scripts/stream_whisper.py

# Google streaming
python scripts/stream_google.py

# Azure continuous recognition
python scripts/stream_azure.py
```

### Format Output

**Plain text:**
```bash
python scripts/transcribe_whisper.py --file audio.wav --output transcript.txt
```

**JSON with metadata:**
```bash
python scripts/transcribe_whisper.py \
  --file audio.wav \
  --format json \
  --output transcript.json

# Output includes:
# - Text segments
# - Timestamps
# - Confidence scores
# - Language detection
```

**SRT subtitles:**
```bash
python scripts/transcribe_whisper.py \
  --file video.mp4 \
  --format srt \
  --output subtitles.srt
```

**VTT subtitles:**
```bash
python scripts/transcribe_whisper.py \
  --file video.mp4 \
  --format vtt \
  --output subtitles.vtt
```

## Common Workflows

### Workflow 1: Meeting Transcription

**Scenario:** Record and transcribe meeting with speaker labels

```bash
# 1. Record meeting
python scripts/record_audio.py \
  --output meeting.wav \
  --vad  # Stop on silence

# 2. Transcribe with speaker diarization
python scripts/transcribe_google.py \
  --file meeting.wav \
  --diarization \
  --speakers 4 \
  --output meeting.json

# 3. Format for readability
python scripts/format_transcript.py \
  --input meeting.json \
  --format markdown \
  --output meeting.md

# Result: Formatted transcript with speaker labels and timestamps
```

### Workflow 2: Voice Notes to Markdown

**Scenario:** Quick voice note → markdown document

```bash
# Record voice note
python scripts/quick_note.py

# (Records audio, transcribes with Whisper, saves as markdown)
# Output: voice-note-2025-01-20-14-30.md
```

### Workflow 3: Batch Transcription

**Scenario:** Transcribe multiple audio files

```bash
# Batch process folder
python scripts/batch_transcribe.py \
  --input ./recordings/ \
  --output ./transcripts/ \
  --engine whisper \
  --model base

# Progress shown for each file
```

### Workflow 4: Video Subtitles

**Scenario:** Generate subtitles for video

```bash
# Extract audio from video
python scripts/extract_audio.py --video lecture.mp4 --output audio.wav

# Generate subtitles
python scripts/transcribe_whisper.py \
  --file audio.wav \
  --format srt \
  --output lecture.srt

# Embed in video (requires ffmpeg)
python scripts/embed_subtitles.py \
  --video lecture.mp4 \
  --subtitles lecture.srt \
  --output lecture-subbed.mp4
```

### Workflow 5: Multi-Language Support

**Scenario:** Transcribe and translate

```bash
# Transcribe Spanish audio
python scripts/transcribe_whisper.py \
  --file spanish-audio.wav \
  --language es \
  --output transcript-es.txt

# Translate to English
python scripts/transcribe_whisper.py \
  --file spanish-audio.wav \
  --task translate \
  --output transcript-en.txt
```

## Whisper Model Sizes

| Model | Parameters | Size | Speed | VRAM | Accuracy |
|-------|------------|------|-------|------|----------|
| **tiny** | 39M | ~75MB | ~32x | ~1GB | Good |
| **base** | 74M | ~142MB | ~16x | ~1GB | Better |
| **small** | 244M | ~466MB | ~6x | ~2GB | Great |
| **medium** | 769M | ~1.5GB | ~2x | ~5GB | Excellent |
| **large** | 1550M | ~2.9GB | 1x | ~10GB | Best |

**Recommendation:**
- **Casual use:** `tiny` or `base` (fast, good enough)
- **Quality needed:** `small` or `medium` (balanced)
- **Professional:** `large` (best accuracy, slower)
- **GPU available:** Use `medium` or `large`
- **CPU only:** Use `tiny` or `base`

## Language Support

**Whisper supports 99+ languages:**
```python
# Common languages
en  # English
es  # Spanish
fr  # French
de  # German
it  # Italian
pt  # Portuguese
nl  # Dutch
pl  # Polish
ru  # Russian
ja  # Japanese
ko  # Korean
zh  # Chinese
ar  # Arabic
hi  # Hindi
```

Full list: [reference/language-codes.md](reference/language-codes.md)

## Speaker Diarization

**Identify who said what:**

```bash
# Google (best diarization)
python scripts/transcribe_google.py \
  --file meeting.wav \
  --diarization \
  --speakers 3  # Hint: 3 speakers expected

# AssemblyAI
python scripts/transcribe_assemblyai.py \
  --file meeting.wav \
  --diarization

# Output format:
# Speaker 1: Hello everyone, let's begin
# Speaker 2: Thanks for joining
# Speaker 1: Today's agenda includes...
```

**Post-process with names:**
```bash
python scripts/label_speakers.py \
  --transcript meeting.json \
  --labels "Alice,Bob,Charlie" \
  --output meeting-labeled.txt
```

## Audio Processing

**Enhance audio quality:**
```bash
# Reduce noise
python scripts/denoise_audio.py \
  --input noisy.wav \
  --output clean.wav

# Normalize volume
python scripts/normalize_audio.py \
  --input quiet.wav \
  --output normalized.wav

# Convert format
python scripts/convert_audio.py \
  --input audio.m4a \
  --output audio.wav
```

## Timestamps and Segments

**Transcript with timestamps:**
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Welcome to today's meeting.",
      "confidence": 0.95
    },
    {
      "start": 3.5,
      "end": 7.2,
      "text": "Let's review the quarterly results.",
      "confidence": 0.92
    }
  ]
}
```

**Search by timestamp:**
```bash
# Find text at specific time
python scripts/find_at_time.py \
  --transcript meeting.json \
  --time "5:30"  # 5 minutes 30 seconds

# Extract time range
python scripts/extract_range.py \
  --transcript meeting.json \
  --start "2:00" \
  --end "5:00" \
  --output excerpt.txt
```

## API Cost Comparison

**Per hour of audio:**
- **Whisper:** Free (local processing)
- **Google:** ~$1.44 (60 min × $0.024/min)
- **Azure:** ~$1.00 (standard pricing)
- **AssemblyAI:** ~$0.90 (3600 sec × $0.00025/sec)

**Free tiers:**
- **Google:** $300 credit (first 90 days)
- **Azure:** 5 hours/month free
- **AssemblyAI:** 3 hours free on signup

## Scripts Reference

**Recording:**
- `record_audio.py` - Record from microphone
- `list_devices.py` - List audio devices
- `test_microphone.py` - Test mic input

**Transcription:**
- `transcribe_whisper.py` - Whisper transcription
- `transcribe_google.py` - Google Cloud STT
- `transcribe_azure.py` - Azure Speech
- `transcribe_assemblyai.py` - AssemblyAI

**Real-time:**
- `stream_whisper.py` - Whisper streaming
- `stream_google.py` - Google streaming
- `stream_azure.py` - Azure continuous

**Processing:**
- `batch_transcribe.py` - Batch processing
- `format_transcript.py` - Format output
- `extract_audio.py` - Extract from video
- `denoise_audio.py` - Noise reduction

**Utilities:**
- `quick_note.py` - Record + transcribe
- `label_speakers.py` - Add speaker names
- `find_at_time.py` - Search by timestamp
- `convert_audio.py` - Format conversion

## Best Practices

1. **Start with Whisper** - Free, offline, good quality
2. **Test different models** - Balance speed vs accuracy
3. **Use VAD** - Voice Activity Detection for cleaner recording
4. **Enhance audio first** - Denoise for better results
5. **Appropriate model size** - Don't use large models for quick notes
6. **Speaker diarization** - Essential for meetings
7. **Save raw audio** - Keep original for re-processing
8. **Add context** - Language hints improve accuracy

## Troubleshooting

**"No module named 'whisper'"**
```bash
pip install openai-whisper --break-system-packages
```

**"Microphone not working"**
```bash
# List devices
python scripts/list_devices.py

# Test specific device
python scripts/test_microphone.py --device 1
```

**"Out of memory" (Whisper)**
```bash
# Use smaller model
python scripts/transcribe_whisper.py --file audio.wav --model tiny

# Or process in chunks
python scripts/transcribe_chunked.py --file large-audio.wav
```

**"Poor transcription quality"**
- Use larger Whisper model (medium/large)
- Enhance audio first (denoise, normalize)
- Specify correct language
- Check microphone quality

**"API authentication failed"**
```bash
# Google
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Azure
export AZURE_SPEECH_KEY="your-key"
export AZURE_SPEECH_REGION="region"

# AssemblyAI
export ASSEMBLYAI_API_KEY="your-key"
```

## Integration Examples

See [examples/](examples/) for complete workflows:
- [examples/meeting-minutes.md](examples/meeting-minutes.md) - Meeting transcription
- [examples/podcast-notes.md](examples/podcast-notes.md) - Podcast processing
- [examples/lecture-subtitles.md](examples/lecture-subtitles.md) - Video subtitles
- [examples/voice-journal.md](examples/voice-journal.md) - Voice note system

## Reference Documentation

- [reference/setup-guide.md](reference/setup-guide.md) - Detailed setup
- [reference/engine-comparison.md](reference/engine-comparison.md) - STT engine details
- [reference/language-codes.md](reference/language-codes.md) - Supported languages
- [reference/api-keys.md](reference/api-keys.md) - Getting API credentials
- [reference/audio-formats.md](reference/audio-formats.md) - Format specifications
