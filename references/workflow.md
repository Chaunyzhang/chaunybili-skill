# Chauny Bilibili Download Workflow

## Goal

Prefer audio-first when collecting Bilibili media. If audio is unavailable or fails, download the Bilibili video to local disk and stop.
Do not mix in transcription, subtitles, or copywriting.

## Working path

1. Use the existing bilibili downloader capability
2. Try MP3 audio first
3. If audio is unavailable or fails verification, fall back to MP4 video
4. Save into a fresh timestamped directory
5. Return the actual file path
6. Verify the file size is greater than zero
7. Stop

## Known working link

- `https://www.bilibili.com/video/BV1xx411c7mD`

## Pitfalls

- Do not let subtitle or ASR steps contaminate this skill
- Use a fresh directory to avoid old-file confusion
- Success means real media exists on disk, not just that a tool returned success
