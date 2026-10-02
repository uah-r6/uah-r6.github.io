"""Cache requested public VOD frames for manual, independent actor review.

Requires optional yt-dlp metadata and imageio-ffmpeg in the research venv.
Metadata URLs expire: refresh with yt-dlp --skip-download --write-info-json.
Frames are visual evidence only and never feed the replay actor resolver.
"""
import argparse
import json
from pathlib import Path
import subprocess

import imageio_ffmpeg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('metadata', type=Path)
    parser.add_argument('seconds', type=float, nargs='+')
    parser.add_argument('--format', default='135')
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text(encoding='utf-8'))
    source = next(f for f in metadata['formats'] if f['format_id'] == args.format)
    stem = args.metadata.name.removesuffix('.info.json')
    for second in args.seconds:
        path = args.metadata.parent / f'{stem}-{second:g}-{args.format}.jpg'
        if path.exists():
            print('cached', path)
            continue
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-ss', str(second),
                        '-i', source['url'], '-frames:v', '1', '-y', str(path)],
                       check=True, capture_output=True, timeout=55)
        print('saved', path)


if __name__ == '__main__':
    main()
