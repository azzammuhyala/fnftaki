# pip install tqdm mutagen fonttools

import os
import zipfile

from datetime import datetime
from mutagen.oggvorbis import OggVorbis
from fontTools.ttLib import TTFont
from tqdm import tqdm
from io import BytesIO

TARGET_SOURCES = (
    'assets', 'helpers', 'previews',
    'changelog.md', 'main.pys', 'options.pys', 'README.md', 'requirements.txt'
)

PARENT_NAME = 'fnftaki'
OUTPUT_NAME = 'taki-v2.1.0.zip'

PNG_IGNORED_CHUNKS = (b'tEXt', b'zTXt', b'iTXt', b'eXIf')
TTF_IDS_TO_REMOVE = (0, 7, 8, 9, 10, 11, 12, 13, 14)

def clean_png(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            return None

        out = BytesIO()
        out.write(data[:8])

        i = 8
        limit = len(data)

        while i < limit:
            if i + 8 > limit:
                break

            length = int.from_bytes(data[i:i + 4], 'big')
            chunk_type = data[i + 4:i + 8]

            if chunk_type not in PNG_IGNORED_CHUNKS:
                out.write(data[i: i + 12 + length])

            i += 12 + length
            if chunk_type == b'IEND':
                break

        return out.getvalue()
    except Exception:
        return None

def clean_webp(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
            return None

        out = BytesIO()
        out.write(data[:12])
        i = 12
        limit = len(data)

        while i < limit:
            if i + 8 > limit:
                break
            chunk_header = data[i:i + 8]
            chunk_type = chunk_header[:4]
            chunk_size = int.from_bytes(chunk_header[4:8], 'little')
            padded_size = chunk_size + (chunk_size % 2)
            total_chunk_length = 8 + padded_size

            if chunk_type not in (b'EXIF', b'XMP ', b'ICCP'):
                out.write(data[i:i + total_chunk_length])

            i += total_chunk_length

        clean_bytes = out.getvalue()
        file_size = len(clean_bytes) - 8
        return clean_bytes[:4] + file_size.to_bytes(4, 'little') + clean_bytes[8:]
    except Exception:
        return None

def clean_ogg(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        io = BytesIO(data)

        audio = OggVorbis(io)
        audio.clear()
        audio.save(io)

        return io.getvalue()
    except Exception:
        return None

def clean_ttf(file_path):
    try:
        font = TTFont(file_path)
        name_table = font['name']
        name_table.names = [n for n in name_table.names if n.nameID not in TTF_IDS_TO_REMOVE]

        io = BytesIO()
        font.save(io)
        return io.getvalue()
    except Exception:
        return None

CLEANERS = {
    'png': clean_png,
    'ogg': clean_ogg,
    'ttf': clean_ttf,
    'webp': clean_webp
}

def collect_files():
    entries = []

    for item in TARGET_SOURCES:
        if not os.path.exists(item):
            continue

        if os.path.isfile(item):
            entries.append((item, os.path.dirname(item) or '.'))
        else:
            base_path = os.path.dirname(item.rstrip(os.sep)) or '.'
            for root, _, files in os.walk(item):
                for file in files:
                    entries.append((os.path.join(root, file), base_path))

    return entries

def main():
    now = datetime.now()
    entries = collect_files()

    with zipfile.ZipFile(OUTPUT_NAME, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        bar = tqdm(entries, unit='file', desc='Packing', ncols=120)

        for file_path, base_path in bar:
            rel_path = os.path.relpath(file_path, base_path)
            if rel_path == '.':
                rel_path = os.path.basename(file_path)

            arcname = os.path.join(PARENT_NAME, rel_path)
            ext = file_path.lower().split('.')[-1]

            bar.set_postfix_str(arcname[:40])

            cleaner = CLEANERS.get(ext)
            clean_data = cleaner(file_path) if cleaner else None

            zinfo = zipfile.ZipInfo(arcname)
            zinfo.date_time = (now.year, now.month, now.day, now.hour, now.minute, now.second)
            zinfo.compress_type = zipfile.ZIP_DEFLATED

            if clean_data:
                zipf.writestr(zinfo, clean_data, compresslevel=9)
            else:
                with open(file_path, 'rb') as f:
                    zipf.writestr(zinfo, f.read(), compresslevel=9)

    print(f"Done. Output saved to: {OUTPUT_NAME}")

if __name__ == '__main__':
    main()