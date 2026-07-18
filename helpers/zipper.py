# pip install tqdm mutagen fonttools

import os
import zipfile
from io import BytesIO
from mutagen.oggvorbis import OggVorbis
from fontTools.ttLib import TTFont
from tqdm import tqdm

TARGET_SOURCES = [
    'assets', 'helpers', 'previews',
    'changelog.md', 'main.pys', 'options.pys', 'README.md', 'requirements.txt'
]

PARENT_DIR_NAME = "fnftaki"
OUTPUT_ZIP = "taki-v2.0.0.zip"

PNG_IGNORED_CHUNKS = [b'tEXt', b'zTXt', b'iTXt', b'eXIf']
TTF_IDS_TO_REMOVE = [0, 7, 8, 9, 10, 11, 12, 13, 14]

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


def clean_ogg(file_path):
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()

        audio_io = BytesIO(file_data)
        audio = OggVorbis(audio_io)
        audio.clear()
        audio.save(audio_io)

        return audio_io.getvalue()
    except Exception:
        return None


def clean_ttf(file_path):
    try:
        font = TTFont(file_path)
        name_table = font['name']
        name_table.names = [n for n in name_table.names if n.nameID not in TTF_IDS_TO_REMOVE]

        font_io = BytesIO()
        font.save(font_io)
        return font_io.getvalue()
    except Exception:
        return None


CLEANERS = {'png': clean_png, 'ogg': clean_ogg, 'ttf': clean_ttf}


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


def process_file(file_path, base_path, zip_file, bar):
    rel_path = os.path.relpath(file_path, base_path)
    if rel_path == '.':
        rel_path = os.path.basename(file_path)

    arcname = os.path.join(PARENT_DIR_NAME, rel_path)
    ext = file_path.lower().split('.')[-1]

    bar.set_postfix_str(arcname[:40])

    cleaner = CLEANERS.get(ext)
    clean_data = cleaner(file_path) if cleaner else None

    if clean_data:
        zip_file.writestr(arcname, clean_data)
    else:
        zip_file.write(file_path, arcname)


def main():
    entries = collect_files()

    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        with tqdm(total=len(entries), unit='file', desc='Packing', ncols=100) as bar:
            for file_path, base_path in entries:
                process_file(file_path, base_path, zipf, bar)
                bar.update(1)

    print(f"Done. Output saved to: {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()