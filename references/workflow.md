# Bilibili Download Workflow

## Goal

Collect Bilibili media safely and verify a real local file exists.

## Preferred path

1. Try audio-first if the user only needs media collection
2. Fall back to video when needed
3. Verify the resulting local file exists and is non-empty

## Hard rules

- Do not mix in publisher actions
- Do not treat a downloader return object as success unless the file exists on disk
