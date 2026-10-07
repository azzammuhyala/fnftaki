import os
from PIL import Image
from pathlib import Path

valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')

def convert_images_to_webp(target_folder, quality=60, max_width=800):
    for filename in os.listdir(target_folder):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(target_folder, filename)
        output_path = os.path.join(target_folder, Path(filename).stem + '.webp')

        try:
            with Image.open(input_path) as img:
                img_data = img.convert('RGB')

                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img_data = img_data.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
                img_data.save(
                    output_path, 
                    'WEBP',
                    quality=quality,
                    method=6
                )

                original_size = os.path.getsize(input_path) / 1024
                converted_size = os.path.getsize(output_path) / 1024
                savings = ((original_size - converted_size) / original_size) * 100
    
                print(f"[OK] {filename:30} | {original_size:7.1f} KB -> {converted_size:6.1f} KB ({savings:5.1f}% smaller)")

            os.remove(input_path)

        except Exception as e:
            print(f"[ERROR] {filename} -> {type(e).__name__}: {e}")

if __name__ == "__main__":
    convert_images_to_webp("previews")