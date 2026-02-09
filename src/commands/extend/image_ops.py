from collections import Counter
from pathlib import Path

from PIL import Image


def get_edge_background_color(img: Image) -> tuple:
    """
    Determines the background color by checking all pixels along the edges.
    """
    width, height = img.size
    # Use RGBA for consistent color representation during calculation
    calc_img = img.convert("RGBA")

    edge_pixels = []

    # Top and Bottom edges
    for x in range(width):
        edge_pixels.append(calc_img.getpixel((x, 0)))
        edge_pixels.append(calc_img.getpixel((x, height - 1)))

    # Left and Right edges (skipping corners already added)
    for y in range(1, height - 1):
        edge_pixels.append(calc_img.getpixel((0, y)))
        edge_pixels.append(calc_img.getpixel((width - 1, y)))

    counts = Counter(edge_pixels)
    most_common_color, _ = counts.most_common(1)[0]
    return most_common_color


def extend_image(image_path: Path, replace: bool = False) -> Path:
    """
    Extends the image to 9x its original size (3x width, 3x height).
    Fills the new area with the detected background color.
    Places the original image in the center.
    """
    with Image.open(image_path) as img:
        bg_color = get_edge_background_color(img)
        width, height = img.size

        new_width = width * 3
        new_height = height * 3

        # We create the new image in RGBA to ensure compatibility with bg_color (which is RGBA)
        # then convert back to original mode if it was RGB.
        new_img = Image.new("RGBA", (new_width, new_height), bg_color)

        # Paste the original image in the center
        # If the original image has an alpha channel, paste() will use it if we provide it as the mask.
        if img.mode == "RGBA":
            new_img.paste(img, (width, height), img)
        else:
            new_img.paste(img, (width, height))

        # Convert back to original mode if appropriate
        if img.mode == "RGB":
            new_img = new_img.convert("RGB")
        elif img.mode not in ("RGB", "RGBA"):
            # For other modes (P, L, etc.), we'll keep it as RGBA or RGB
            # to avoid issues with the identified background color.
            pass

        if replace:
            target_path = image_path
        else:
            target_path = image_path.parent / f"{image_path.stem}_extended{image_path.suffix}"

        new_img.save(target_path)

    return target_path
