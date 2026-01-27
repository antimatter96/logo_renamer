from pathlib import Path

from PIL import Image, ImageChops


def trim_image(image_path: Path, margin: int, replace: bool = False) -> Path:
    """
    Trims the image by removing the border of the background color.
    The background color is determined from the top-left pixel.
    Adds a specified margin around the cropped content.
    Returns the path to the saved image.
    """
    with Image.open(image_path) as img:
        # Process in RGBA to handle transparency correctly if present,
        # or just to have a consistent color space for diffing.
        # However, we want to crop the ORIGINAL image object to preserve its mode if possible,
        # or at least save it back in a compatible way.

        # We use a copy for calculation to not mess up the original if we needed to convert
        calc_img = img.convert("RGBA")
        bg_color = calc_img.getpixel((0, 0))

        # Create a background image with the same color
        bg = Image.new("RGBA", calc_img.size, bg_color)

        # Calculate difference
        diff = ImageChops.difference(calc_img, bg)
        # Get bounding box of non-zero difference
        bbox = diff.getbbox()

        if not bbox:
            # If bbox is None, it could be because the alpha channel difference is 0
            # (e.g. opaque image against opaque background), so getbbox() sees it as "empty".
            # Check RGB channels for difference.
            bbox = diff.convert("RGB").getbbox()

        if not bbox:
            # Image is entirely the background color (or empty)
            # Just return original
            return image_path

        # Expand bbox with margin
        left, upper, right, lower = bbox
        width, height = img.size

        left = max(0, left - margin)
        upper = max(0, upper - margin)
        right = min(width, right + margin)
        lower = min(height, lower + margin)

        # Crop the ORIGINAL image (img)
        cropped = img.crop((left, upper, right, lower))

        # Save
        if replace:
            target_path = image_path
        else:
            target_path = image_path.parent / f"{image_path.stem}_trimmed{image_path.suffix}"

        cropped.save(target_path)

    return target_path
