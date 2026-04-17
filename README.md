# Chauny Bilibili Skill

A consolidated Bilibili skill rebuilt from the upstream `bilibili-all-in-one` capability set, but now maintained as a self-contained local core inside this repository.

## Safety default

This aggregated repo is read-mostly by default.

The following high-risk write operations are intentionally not exposed as first-class workflows here:

- publish video
- edit published video
- draft upload
- scheduled publish

The upstream capability was absorbed into this repository's own local core, but write-heavy publisher actions are still treated as disabled by default.

## What this repo can do today

- hot/trending monitoring
- video or audio downloading
- video stats and comparison
- subtitle listing/downloading/conversion/merge
- playback URL, playlist, and danmaku fetching
- optional DashScope transcription for local media or public audio URLs

## Install

```bash
python -m pip install -r requirements.txt
```

Optional:

```bash
ffmpeg
```

Needed only for:

- local file transcription normalization

## Status first

```bash
python scripts/bili_status.py --json
```

Read-only work is ready when:

- `impl_package_exists: true`
- `read_only_ready: true`

## Credentials

Most read-only workflows do not require credentials.

If you want to use authenticated features in the future, provide:

- `BILIBILI_SESSDATA`
- `BILIBILI_BILI_JCT`
- `BILIBILI_BUVID3`

or place them in:

```text
~/.local/share/chaunybili-skill/credentials.json
```

## Workflows

### Hot monitor

```bash
python scripts/bili_hot.py --mode hot --page-size 10
python scripts/bili_hot.py --mode rank --category game --limit 10
```

### Download

```bash
python scripts/bili_download.py "https://www.bilibili.com/video/BV1xx411c7mD" --format mp3
python scripts/bili_download.py "https://www.bilibili.com/video/BV1xx411c7mD" --format mp4
```

### Stats and comparison

```bash
python scripts/bili_watch.py --mode stats "BV1xx411c7mD"
python scripts/bili_watch.py --mode compare "BV1xx411c7mD,BV1yy411c8nE"
```

### Subtitle workflow

```bash
python scripts/bili_subtitle.py --mode list "BV1xx411c7mD"
python scripts/bili_subtitle.py --mode download "BV1xx411c7mD" --language zh-CN --format srt
```

### Player workflow

```bash
python scripts/bili_play.py --mode play "BV1xx411c7mD"
python scripts/bili_play.py --mode danmaku "BV1xx411c7mD"
```

### Transcription workflow

```bash
python scripts/bili_transcribe.py "D:/path/to/video.mp4"
python scripts/bili_transcribe.py "https://example.com/audio.wav"
```

## Detailed operator manual

Read this before handing the repo to a weaker model:

- `references/OPERATIONS-MANUAL.md`
