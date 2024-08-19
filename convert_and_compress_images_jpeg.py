import os

# pip install pillow
from PIL import Image

def convert_png_to_jpeg(png_path, jpeg_path, quality=85):
    try:
        with Image.open(png_path) as img:
            # Ensure the image is in RGB mode
            rgb_im = img.convert('RGB')
            # Save the image as a JPEG with the desired quality
            rgb_im.save(jpeg_path, 'JPEG', quality=quality)
            print(f"Converted {png_path} to {jpeg_path}")
    except Exception as e:
        print(f"Failed to convert {png_path}: {e}")

def batch_convert_png_to_jpeg(input_dir, output_dir, quality=85):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.png'):
                png_path = os.path.join(root, file)
                jpeg_filename = os.path.splitext(file)[0] + '.jpg'
                jpeg_path = os.path.join(output_dir, jpeg_filename)

                convert_png_to_jpeg(png_path, jpeg_path, quality)

# Example usage
input_directory = r'F:\temp'
output_directory = r'F:\temp2'

# Start the batch conversion process
batch_convert_png_to_jpeg(input_directory, output_directory, quality=85)
