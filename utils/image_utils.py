from PIL import Image
import os

def crop_and_save_square_image(image_file, save_path, size=1000):
    """
    Crops the given image to a square from the center, resizes it to 1000x1000 (default),
    and saves it as JPEG. Converts from RGBA to RGB if needed for JPEG compatibility.
    """
    img = Image.open(image_file).convert("RGBA")
    width, height = img.size
    min_side = min(width, height)

    # Crop to center square
    left = (width - min_side) / 2
    top = (height - min_side) / 2
    right = (width + min_side) / 2
    bottom = (height + min_side) / 2

    img_cropped = img.crop((left, top, right, bottom)).resize((size, size))

    # Convert RGBA to RGB (remove transparency for JPEG)
    if img_cropped.mode == "RGBA":
        background = Image.new("RGB", img_cropped.size, (255, 255, 255))
        background.paste(img_cropped, mask=img_cropped.split()[3])
        img_cropped = background

    img_cropped.save(save_path, format="JPEG")

def delete_profile_image(path):
    """
    Deletes the given image file if it exists.
    """
    if path and os.path.exists(path):
        os.remove(path)