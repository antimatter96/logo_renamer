from pathlib import Path
import typer
from rich.console import Console
from PIL import Image, ImageChops

from src.shared import image_ops

console = Console()


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


def trim(

    image_path: Path = typer.Argument(..., help="Path to the image file or directory."),
    margin: int = typer.Option(10, help="Margin in pixels to leave around the content."),
    replace: bool = typer.Option(
        False,
        "--replace",
        "-r",
        help="Replace the original file instead of creating a new one.",
    ),
):
    """
    Trims the background from an image or a directory of images.
    Identifies the background color from the top-left pixel.
    """
    if image_path.is_dir():
        # Bulk processing
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
        files_to_process = [
            p
            for p in image_path.iterdir()
            if p.is_file() and p.suffix.lower() in valid_extensions
        ]

        if not files_to_process:
            console.print(f"[bold yellow]Warning:[/] No image files found in {image_path}")
            return

        console.print(
            f"[bold blue]Bulk Trimming:[/] Found {len(files_to_process)} images in {image_path}"
        )

        for file_path in files_to_process:
            try:
                output_path = trim_image(file_path, margin, replace)
                console.print(f"[bold green]Trimmed:[/] {file_path.name} -> {output_path.name}")
            except Exception as e:
                console.print(f"[bold red]Error trimming {file_path.name}:[/] {e}")

    else:
        # Single file processing
        try:
            output_path = trim_image(image_path, margin, replace)
            console.print(f"[bold green]Trimmed:[/] {image_path.name} -> {output_path.name}")
        except Exception as e:
            console.print(f"[bold red]Error trimming {image_path.name}:[/] {e}")
            raise typer.Exit(code=1)
