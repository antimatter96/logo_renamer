from pathlib import Path
from PIL import Image

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
