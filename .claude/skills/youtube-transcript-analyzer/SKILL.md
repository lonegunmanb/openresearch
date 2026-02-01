---
name: youtube-transcript-analyzer
description: "Use when analyzing YouTube videos for research or learning"
version: 0.5.0
category: research
triggers:
  - "youtube"
  - "video transcript"
  - "analyze video"
  - "watch this"
  - "youtube.com"
  - "youtu.be"
---

<objective>
Download and analyze YouTube video transcripts to extract insights, understand concepts, and relate content to your work. Uses yt-dlp for reliable transcript extraction with intelligent chunking for long-form content.
</objective>

<when-to-use>
Use when you need to understand how a YouTube video/tutorial relates to your current project, research technical concepts explained in video format, extract key insights from talks or presentations, compare video content with your codebase or approach, or learn from video demonstrations without watching the entire video.
</when-to-use>

<prerequisites>
Ensure yt-dlp is installed:

```bash
# Install via pip
pip install yt-dlp

# Or via homebrew (macOS)
brew install yt-dlp

# Verify installation
yt-dlp --version
```

</prerequisites>

<transcript-extraction>
Setup temporary directory - IMPORTANT: Always create and use a temporary directory for downloaded files to avoid cluttering the repository:

```bash
# Create temporary directory for this analysis
ANALYSIS_DIR=$(mktemp -d)
echo "Using temporary directory: $ANALYSIS_DIR"
```

Download transcript using yt-dlp to extract subtitles/transcripts to the temporary
directory:

```bash
# Download transcript only (no video)
yt-dlp --skip-download --write-auto-sub --sub-format vtt --output "$ANALYSIS_DIR/transcript.%(ext)s" URL

# Or get manually created subtitles if available (higher quality)
yt-dlp --skip-download --write-sub --sub-lang en --sub-format vtt --output "$ANALYSIS_DIR/transcript.%(ext)s" URL

# Get video metadata for context
yt-dlp --skip-download --print-json URL > "$ANALYSIS_DIR/metadata.json"
```

Handle long transcripts - For transcripts exceeding 8,000 tokens (roughly 6,000 words or
45+ minutes):

1. Split into logical chunks based on timestamp or topic breaks
2. Generate a summary for each chunk focusing on key concepts
3. Create an overall synthesis connecting themes to the user's question
4. Reference specific timestamps for detailed sections

For shorter transcripts, analyze directly without chunking. </transcript-extraction>

<analysis-approach>
When analyzing with respect to a project or question:
1. Extract the video's core concepts and techniques
2. Identify patterns, architectures, or approaches discussed
3. Compare with the current project's implementation
4. Highlight relevant insights, differences, and potential applications
5. Note specific timestamps for key moments

Provide analysis in this format:

Video Overview:

- Title, author, duration
- Main topic and key themes

Key Insights:

- Concept 1 with timestamp
- Concept 2 with timestamp
- Technical approaches explained

Relevance to Your Project:

- Direct applications
- Differences from current approach
- Potential improvements or learnings

Specific Recommendations:

- Actionable items based on video content
- Code patterns or techniques to consider </analysis-approach>

<handling-common-issues>
No transcript available: Some videos lack auto-generated or manual captions. When yt-dlp cannot extract subtitles, use the NotebookLM fallback workflow described below.

Multiple languages: Prefer English transcripts using --sub-lang en. If unavailable,
check available languages with --list-subs.

Long processing time: Set expectations for videos over 2 hours. Offer to focus on
specific sections if timestamps provided. </handling-common-issues>

<notebooklm-fallback>
When yt-dlp fails to extract subtitles (no auto-generated or manual captions available), use the `notebooklm` skill as a fallback to extract the video transcript.

**Prerequisites:** Refer to the `notebooklm` skill documentation for authentication and CLI usage details.

**Workflow:**

1. **Create a temporary notebook** with a unique name (e.g., include timestamp)
   - Parse the `id` from the JSON output and save it for cleanup later

2. **Add the YouTube video as a source**
   - Parse the `source_id` from the output

3. **Wait for source processing**
   - Use retry loop with **maximum total wait time: 30 minutes**
   - If 30 minutes elapsed and still processing, treat as failure
   - Refer to "Source Wait with Retry Logic" section in `notebooklm` skill for implementation details

4. **Request transcript via chat**
   - **Important:** The prompt language should match the end user's language
   - Ask NotebookLM to output the complete transcript with timestamps, not a summary
   - If NotebookLM responds that the video is too long to process, inform the caller: **"This video is too long to process. NotebookLM cannot generate a complete transcript for videos of this length."**

5. **Cleanup (MANDATORY)**
   
   ⚠️ **CRITICAL:** The agent MUST NOT exit without deleting the temporary notebook. Always ensure cleanup happens:
   - If transcript extraction succeeds → delete notebook → return transcript
   - If transcript extraction fails → delete notebook → report failure
   - If any error occurs → delete notebook → report error

**Error Handling:**

| Scenario | Action |
|----------|--------|
| Source processing fails | Delete notebook, report "Video could not be processed by NotebookLM" |
| Source processing timeout (30 min) | Delete notebook, report "Video processing timed out after 30 minutes" |
| NotebookLM says video too long | Delete notebook, report "This video is too long to process" |
| Chat returns partial transcript | Use what's available, delete notebook, continue with analysis |
| Any unexpected error | Delete notebook, report the error |
</notebooklm-fallback>

<stt-transcription-fallback>
When NotebookLM reports that the video is too long to process, use the `stt-transcription` skill as the final fallback to generate a transcript from the audio.

**Prerequisites:**
- `yt-dlp` for downloading audio
- `ffmpeg` for audio conversion
- Azure Speech SDK or other STT engine

**Workflow:**

1. **Download audio using youtube-downloader skill**
   ```bash
   python .claude/skills/youtube-downloader/scripts/download_video.py "VIDEO_URL" -a -o "OUTPUT_DIR"
   ```
   - This downloads the audio as MP3

2. **Convert MP3 to WAV format (required for Azure Speech)**
   ```bash
   ffmpeg -i "audio.mp3" -acodec pcm_s16le -ar 16000 -ac 1 "audio.wav" -y
   ```
   - Azure Speech requires 16kHz mono PCM WAV format

3. **Transcribe using stt-transcription skill**
   - Invoke the `stt-transcription` skill
   - Prefer Azure Speech for cloud transcription (see stt-transcription SKILL.md for Azure CLI usage)
   - For local/free option, use Whisper

4. **Cleanup temporary files**
   - Delete intermediate webm, wav files after transcription
   - Keep only the final mp3 (if needed) and transcript

**Error Handling:**

| Scenario | Action |
|----------|--------|
| yt-dlp download fails | Report "Could not download audio from this video" |
| ffmpeg conversion fails | Check ffmpeg installation, report error |
| Azure Speech fails | Fall back to Whisper local transcription |
| Transcription timeout | Report partial results if available |

**Language Detection:**
- For Chinese content, use `zh-CN` language code
- For English content, use `en-US` language code
- Match the language code to the video's spoken language
</stt-transcription-fallback>

<transcript-extraction-priority>
When extracting transcripts from YouTube videos, follow this priority order:

1. **yt-dlp subtitles (fastest, most reliable)**
   - Try manual subtitles first (`--write-sub`)
   - Fall back to auto-generated subtitles (`--write-auto-sub`)
   
2. **NotebookLM (for videos without subtitles)**
   - Works for most video lengths
   - May fail for very long videos (2+ hours)
   
3. **STT Transcription (final fallback)**
   - Download audio → Convert to WAV → Transcribe
   - Most resource-intensive but always works
   - Prefer Azure Speech for accuracy, Whisper for free/local
</transcript-extraction-priority>

<best-practices>
Focus analysis on practical application rather than comprehensive summaries. Users want to know "how does this help me" not "what did they say for 90 minutes."

Extract concrete examples and code patterns when available. Reference specific
timestamps so users can jump to relevant sections.

When comparing with project code, be specific about similarities and differences. Vague
comparisons like "similar approach" don't add value.

For technical content, identify the underlying patterns and principles rather than
surface-level implementation details. Help users understand transferable concepts.
</best-practices>

<token-efficiency>
For very long transcripts (2+ hours):
- Process in 15-20 minute segments
- Summarize each segment to 200-300 words
- Create final synthesis under 500 words
- Provide detailed analysis only for highly relevant sections
</token-efficiency>