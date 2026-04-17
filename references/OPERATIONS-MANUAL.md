# Chauny Bilibili Skill Operations Manual

This manual is written for weaker models and low-context operators.

## 1. Purpose

This repo is a self-contained Bilibili aggregated skill.

It no longer depends on a hardcoded external `bilibili-all-in-one` install path.
Instead, it keeps a repo-owned local implementation subset under `bili_impl/`.

Safe-by-default blocks:

1. hot monitor
2. media download
3. stats and comparison
4. subtitles
5. playback and danmaku
6. optional transcription

Default disabled block:

7. publishing and edit actions

## 2. First command

Always run:

```bash
python scripts/bili_status.py --json
```

Read-only ready means:

- `impl_package_exists: true`
- `read_only_ready: true`

## 3. Safety default

Do not run publisher actions by default.

The upstream code supports publishing, but this aggregated repo intentionally keeps publishing outside the default workflow because it is a high-risk write path.

## 4. Install

```bash
python -m pip install -r requirements.txt
```

Optional:

```bash
ffmpeg
```

Needed for local-file transcription normalization.

## 5. Credentials

Most read-only Bilibili flows do not require credentials.

Optional credentials:

- `BILIBILI_SESSDATA`
- `BILIBILI_BILI_JCT`
- `BILIBILI_BUVID3`

They may also be stored in:

```text
~/.local/share/chaunybili-skill/credentials.json
```

If credentials are absent, do not stop read-only flows automatically.

## 6. Workflow map

### Hot monitor

```bash
python scripts/bili_hot.py --mode hot --page-size 10
python scripts/bili_hot.py --mode trending --limit 10
python scripts/bili_hot.py --mode rank --category game --limit 10
```

### Download

```bash
python scripts/bili_download.py "<url>" --format mp3
python scripts/bili_download.py "<url>" --format mp4
```

### Stats

```bash
python scripts/bili_watch.py --mode stats "<url_or_bvid>"
python scripts/bili_watch.py --mode compare "<url1>,<url2>"
```

### Subtitles

```bash
python scripts/bili_subtitle.py --mode list "<url_or_bvid>"
python scripts/bili_subtitle.py --mode download "<url_or_bvid>" --language zh-CN --format srt
python scripts/bili_subtitle.py --mode convert "<subtitle_path>" --format vtt
```

### Playback

```bash
python scripts/bili_play.py --mode play "<url_or_bvid>"
python scripts/bili_play.py --mode playurl "<url_or_bvid>"
python scripts/bili_play.py --mode danmaku "<url_or_bvid>"
python scripts/bili_play.py --mode playlist "<url_or_bvid>"
```

### Transcription

```bash
python scripts/bili_transcribe.py "D:/path/to/video.mp4"
python scripts/bili_transcribe.py "https://example.com/audio.wav"
```

## 7. Known realities

### This repo is safer than the old wrapper

The old wrapper failed because it imported a hardcoded path outside the repo.

This repo now owns the implementation subset locally.

### Some high-quality downloads may still need credentials

Do not assume credentials are required for every download.
Only escalate to credential setup when the exact target needs it.

### ffmpeg is not required for normal download

It is only required for local-video transcription.

## 8. Practical acceptance checklist

Safe checks:

1. `bili_status.py --json`
2. `bili_hot.py`
3. `bili_download.py`
4. `bili_watch.py`
5. `bili_subtitle.py`
6. `bili_play.py`
7. `bili_transcribe.py`

Do not treat publisher support as part of the normal acceptance checklist.
