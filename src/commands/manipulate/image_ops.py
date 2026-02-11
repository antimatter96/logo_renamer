from collections import Counter

from PIL import Image, ImageChops

from src.shared.image_ops import ImageValidationError


def get_edge_background_color(img: Image.Image) -> tuple:
    """
    Determines the background color by checking all pixels along the edges.
    """
    width, height = img.size
    calc_img = img.convert("RGBA")
    edge_pixels = []

    for x in range(width):
        edge_pixels.append(calc_img.getpixel((x, 0)))
        edge_pixels.append(calc_img.getpixel((x, height - 1)))

    for y in range(1, height - 1):
        edge_pixels.append(calc_img.getpixel((0, y)))
        edge_pixels.append(calc_img.getpixel((width - 1, y)))

    counts = Counter(edge_pixels)
    return counts.most_common(1)[0][0]


def get_corner_background_color(img: Image.Image) -> tuple:
    """
    Determines background color from 4 corners.
    Returns the color if at least 3 match, else raises ImageValidationError.
    """
    width, height = img.size
    calc_img = img.convert("RGBA")
    corners = [
        calc_img.getpixel((0, 0)),
        calc_img.getpixel((width - 1, 0)),
        calc_img.getpixel((0, height - 1)),
        calc_img.getpixel((width - 1, height - 1)),
    ]
    corner_counts = Counter(corners)
    most_common_bg, count = corner_counts.most_common(1)[0]
    if count < 3:
        raise ImageValidationError("Inconsistent background color: fewer than 3 corners match.")
    return most_common_bg


def trim_image_obj(img: Image.Image, margin: int) -> tuple[Image.Image, bool]:
    """
    Trims the image background. Returns (new_image, was_modified).
    """
    calc_img = img.convert("RGBA")
    width, height = calc_img.size
    bg_color = get_corner_background_color(calc_img)

    bg = Image.new("RGBA", calc_img.size, bg_color)
    diff = ImageChops.difference(calc_img, bg)
    bbox = diff.getbbox()

    if not bbox:
        bbox = diff.convert("RGB").getbbox()

    if not bbox:
        return img, False

    left, upper, right, lower = bbox
    left = max(0, left - margin)
    upper = max(0, upper - margin)
    right = min(width, right + margin)
    lower = min(height, lower + margin)

    if (left, upper, right, lower) == (0, 0, width, height):
        return img, False

    return img.crop((left, upper, right, lower)), True


def extend_image_obj(img: Image.Image) -> Image.Image:
    """
    Extends the image to 9x its size, centered.
    """
    bg_color = get_edge_background_color(img)
    width, height = img.size
    new_width, new_height = width * 3, height * 3

    new_img = Image.new("RGBA", (new_width, new_height), bg_color)
    if img.mode == "RGBA":
        new_img.paste(img, (width, height), img)
    else:
        new_img.paste(img, (width, height))

    if img.mode == "RGB":
        return new_img.convert("RGB")
    return new_img
