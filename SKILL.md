---
name: chaunybili-skill
description: 一个聚合版 Bilibili 技能，包含热点监控、下载、数据分析、字幕、播放信息、可选 DashScope 转写等只读能力。默认禁用发布类写操作。适合弱模型按步骤执行：先检查状态，再选择热点、下载、字幕、播放或转写工作流。
---

# Chauny Bilibili Skill

Detailed operator manual:

- `references/OPERATIONS-MANUAL.md`

## First rule

Always check status first:

```bash
python scripts/bili_status.py --json
```

Then prepare the reusable workflow state:

```bash
python scripts/bili_prepare.py
```

Do not choose a workflow before the status check succeeds.

## Safety default

Do not use publisher actions as the default workflow.
Treat this repo as read-mostly unless the user explicitly asks for a risky write operation and accepts the platform-risk tradeoff.

## Workflow A: hot monitor

```bash
python scripts/bili_hot.py --mode hot --page-size 10
python scripts/bili_hot.py --mode rank --category game --limit 10
```

## Workflow B: media download

```bash
python scripts/bili_download.py "<bilibili_url>" --format mp3
python scripts/bili_download.py "<bilibili_url>" --format mp4
```

## Workflow C: stats and comparison

```bash
python scripts/bili_watch.py --mode stats "<bilibili_url_or_bvid>"
python scripts/bili_watch.py --mode compare "<url1>,<url2>"
```

## Workflow D: search

```bash
python scripts/bili_search.py "<keyword>" --page-size 10
```

## Workflow E: comments

```bash
python scripts/bili_comments.py "<bilibili_url_or_bvid>" --page-size 10 --sort 2
```

## Workflow F: creator analysis

```bash
python scripts/bili_creator.py "<mid>" --mode profile
```

Do not use `--mode videos` by default.
It is temporarily disabled until there is a lower-risk and more stable path.

## Workflow G: subtitles

```bash
python scripts/bili_subtitle.py --mode list "<bilibili_url_or_bvid>"
python scripts/bili_subtitle.py --mode download "<bilibili_url_or_bvid>" --language zh-CN --format srt
```

## Workflow H: playback and danmaku

```bash
python scripts/bili_play.py --mode play "<bilibili_url_or_bvid>"
python scripts/bili_play.py --mode danmaku "<bilibili_url_or_bvid>"
```

## Workflow I: transcription

```bash
python scripts/bili_transcribe.py "<local_or_remote_media_source>"
```

## Weak-model rules

1. Do not skip `bili_status.py`
2. Assume read-only mode unless the user explicitly overrides it
3. Prefer MP3 download first when the user only needs content collection
4. Keep publisher capability disabled in normal runs
