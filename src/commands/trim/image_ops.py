from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops

from src.shared.image_ops import ImageValidationError


def trim_image(image_path: Path, margin: int, replace: bool = False) -> tuple[Path, bool]:
    """
    Trims the image by removing the border of the background color.
    The background color is determined by checking all 4 corners;
    at least 3 must match to proceed.
    Adds a specified margin around the cropped content.
    Returns (path_to_saved_image, was_modified).
    """
    with Image.open(image_path) as img:
        # Process in RGBA to handle transparency correctly if present,
        # or just to have a consistent color space for diffing.
        # However, we want to crop the ORIGINAL image object to preserve its mode if possible,
        # or at least save it back in a compatible way.

        # We use a copy for calculation to not mess up the original if we needed to convert
        calc_img = img.convert("RGBA")
        width, height = calc_img.size

        # Check all 4 corners to determine background color
        corners = [
            calc_img.getpixel((0, 0)),
            calc_img.getpixel((width - 1, 0)),
            calc_img.getpixel((0, height - 1)),
            calc_img.getpixel((width - 1, height - 1)),
        ]

        # Determine if we have a consistent background (>= 3 corners match)
        corner_counts = Counter(corners)
        most_common_bg, count = corner_counts.most_common(1)[0]

        if count < 3:
            raise ImageValidationError(
                "Inconsistent background color: fewer than 3 corners match."
            )

        bg_color = most_common_bg

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
            return image_path, False

        # Expand bbox with margin
        left, upper, right, lower = bbox

        left = max(0, left - margin)
        upper = max(0, upper - margin)
        right = min(width, right + margin)
        lower = min(height, lower + margin)

        # Check if the new dimensions are actually different
        if (left, upper, right, lower) == (0, 0, width, height):
            return image_path, False

        # Crop the ORIGINAL image (img)
        cropped = img.crop((left, upper, right, lower))

        # Save
        if replace:
            target_path = image_path
        else:
            target_path = image_path.parent / f"{image_path.stem}_trimmed{image_path.suffix}"

        cropped.save(target_path)

    return target_path, True
