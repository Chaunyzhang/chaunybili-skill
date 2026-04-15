---
name: chaunybili-skill
description: Chauny's Bilibili collection skill. Prefer audio-first when collecting B站 media, and fall back to video when audio download is unavailable or fails. Then verify the chosen file really exists. Use when the user wants to collect Bilibili media first, before any transcription or copywriting step. Do not use this skill for ASR or text generation.
---

Read `references/workflow.md` before changing the workflow.

## Command

```bash
python scripts/download_bilibili_video.py "<bilibili_url>" "<optional_output_dir>"
```

## Hard rules

- Only do download and verification.
- Prefer audio-first, video fallback.
- Success requires a real local file with size > 0.
- Do not mix in subtitles or transcription.
- If verification fails, treat the run as failed.
