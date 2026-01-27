from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops


class ImageValidationError(Exception):
    pass


def load_and_validate_image(image_path: Path) -> bytes:
    """
    Validates that the file exists and is a valid image.
    Returns the file bytes if valid.
    Raises ImageValidationError if invalid.
    """
    if not image_path.exists():
        raise ImageValidationError(f"File '{image_path}' does not exist.")

    try:
        # Verify it's an image
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        raise ImageValidationError(f"Invalid image file '{image_path}': {e}")

    # Read bytes
    try:
        with open(image_path, "rb") as f:
            return f.read()
    except Exception as e:
        raise ImageValidationError(f"Could not read file '{image_path}': {e}")


def get_mime_type(image_path: Path) -> str:
    """
    Returns a simple mime type based on extension.
    """
    # Simple inference, sufficient for the GenAI API usage here
    # Remove the dot
    suffix = image_path.suffix.lstrip(".").lower()
    if suffix == "jpg":
        suffix = "jpeg"
    return f"image/{suffix}"


def determine_new_path(image_path: Path, company_name: str) -> Path:
    """
    Constructs the desired new path based on company name.
    """
    extension = image_path.suffix
    new_filename = f"{company_name}{extension}"
    return image_path.parent / new_filename


def rename_image(image_path: Path, target_path: Path) -> Path:
    """
    Renames the image to target_path.
    If target_path exists, appends a timestamp to avoid collision.
    Returns the actual path the file was renamed to.
    Raises FileExistsError if it still collides (unlikely but possible).
    """
    final_path = target_path

    if final_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # target_path.stem is the company name
        new_filename = f"{target_path.stem}_{timestamp}{target_path.suffix}"
        final_path = target_path.parent / new_filename

        if final_path.exists():
            raise FileExistsError(f"Collision even with timestamp: {final_path.name}")

    image_path.rename(final_path)
    return final_path


def trim_image(image_path: Path, margin: int = 10, replace: bool = False) -> Path:
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
