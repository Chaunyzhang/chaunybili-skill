import asyncio
import json
import os
import sys
import time

sys.path.insert(0, r'C:\Users\ye302\AppData\Roaming\npm\node_modules\openclaw\skills\bilibili-all-in-one')
from main import BilibiliAllInOne


async def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "missing_url"}, ensure_ascii=False))
        return 1

    url = sys.argv[1]
    base_output_dir = sys.argv[2] if len(sys.argv) >= 3 else r'C:\Users\ye302\.openclaw\workspace-klmk\bili-download-test'
    output_dir = os.path.join(base_output_dir, str(int(time.time())))
    os.makedirs(output_dir, exist_ok=True)

    app = BilibiliAllInOne()
    audio_result = await app.execute('downloader', 'download', url=url, output_dir=output_dir, format='mp3')
    audio_path = audio_result.get('filepath') or audio_result.get('file_path') or ''
    audio_size = int(audio_result.get('file_size_bytes') or 0) or (os.path.getsize(audio_path) if (audio_path and os.path.exists(audio_path)) else 0)

    selected_kind = 'audio'
    result = audio_result
    file_path = audio_path
    size = audio_size

    if not (bool(audio_result.get('success')) and audio_size > 0):
        video_result = await app.execute('downloader', 'download', url=url, output_dir=output_dir)
        video_path = video_result.get('filepath') or video_result.get('file_path') or ''
        video_size = int(video_result.get('file_size_bytes') or 0) or (os.path.getsize(video_path) if (video_path and os.path.exists(video_path)) else 0)
        result = video_result
        file_path = video_path
        size = video_size
        selected_kind = 'video'

    exists = size > 0

    payload = {
        'platform': 'bilibili',
        'source_url': url,
        'success': bool(result.get('success')) and exists,
        'media_kind': selected_kind,
        'file_path': file_path,
        'file_size_bytes': size,
        'raw_result': result,
        'notes': 'audio first, video fallback; success means downloader returned success and file size > 0',
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload['success'] else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
