from pathlib import Path

import typer
from PIL import Image, ImageChops
from rich.console import Console

from src.shared.image_ops import (
    ImageValidationError,
    load_and_validate_image,
)

from .image_ops import extend_image_obj, trim_image_obj

console = Console()


def parse_operations(ops_str: str) -> list[tuple]:
    """
    Parses 'e,t48' into [('e', None), ('t', 48)]
    """
    ops = []
    for part in ops_str.split(","):
        part = part.strip().lower()
        if not part:
            continue
        if part == "e":
            ops.append(("e", None))
        elif part.startswith("t"):
            try:
                margin = int(part[1:]) if len(part) > 1 else 20
                ops.append(("t", margin))
            except ValueError:
                raise ValueError(f"Invalid trim margin: {part[1:]}")
        else:
            raise ValueError(f"Unknown operation: {part}")
    return ops


def _images_are_identical(img1: Image.Image, img2: Image.Image) -> bool:
    """
    Performs a pixel-perfect comparison between two images.
    """
    if img1.size != img2.size or img1.mode != img2.mode:
        return False

    diff = ImageChops.difference(img1, img2)
    return not diff.getbbox()


def _process_single_file(
    image_path: Path, ops: list[tuple], replace: bool, skip_same: bool
) -> str:
    """
    Applies a sequence of operations to an image.
    Returns status: 'processed', 'no_change', or 'skipped'.
    """
    try:
        load_and_validate_image(image_path)
    except ImageValidationError as e:
        console.print(f"[bold red]Skip {image_path.name}:[/ ] {e}")
        return "skipped"

    try:
        with Image.open(image_path) as img:
            original_img = img.copy()
            current_img = original_img.copy()
            modified = False

            for op_type, param in ops:
                if op_type == "e":
                    current_img = extend_image_obj(current_img)
                    modified = True
                elif op_type == "t":
                    current_img, was_trimmed = trim_image_obj(current_img, param)
                    if was_trimmed:
                        modified = True

            # Check if final image is same as source if requested
            if modified and skip_same:
                if _images_are_identical(original_img, current_img):
                    modified = False

            if not modified:
                console.print(f"[bold yellow]Warning:[/ ] No changes for {image_path.name}")
                return "no_change"

            if replace:
                target_path = image_path
            else:
                suffix = f"_processed{image_path.suffix}"
                target_path = image_path.parent / f"{image_path.stem}{suffix}"

            current_img.save(target_path)
            console.print(f"[bold green]Processed:[/ ] {image_path.name} -> {target_path.name}")
            return "processed"

    except Exception as e:
        console.print(f"[bold red]Error processing {image_path.name}:[/ ] {e}")
        return "skipped"


def manipulate(
    ops_str: str = typer.Argument(
        ...,
        help="Comma-separated operations: 'e' (extend), 't<margin>' (trim). Examples: 'e', 't20', 'e,t48'",
    ),
    image_paths: list[Path] = typer.Argument(..., help="Path to image file(s) or directories."),
    replace: bool = typer.Option(
        False, "--replace", "-r", help="Replace the original file(s)."
    ),
    skip_same: bool = typer.Option(
        True,
        "--skip-same/--no-skip-same",
        help="Skip saving if the final image is identical to the source.",
    ),
):
    """
    Manipulate images with a sequence of operations.

    Examples:

    - Trim with 20px margin: 't20'
    - Extend background then trim with 48px margin: 'e,t48'
    - Just extend: 'e'
    """
    try:
        ops = parse_operations(ops_str)
    except ValueError as e:
        console.print(f"[bold red]Error parsing operations:[/ ] {e}")
        return

    files_to_process = []
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

    for path in image_paths:
        if path.is_dir():
            dir_files = [
                p
                for p in path.iterdir()
                if p.is_file() and p.suffix.lower() in valid_extensions
            ]
            files_to_process.extend(dir_files)
        elif path.exists():
            files_to_process.append(path)
        else:
            console.print(f"[bold red]Error:[/ ] Path not found: {path}")

    if not files_to_process:
        console.print("[bold yellow]Warning:[/ ] No images found to process.")
        return

    processed_count = 0
    no_change_count = 0
    skipped_count = 0

    for file_path in files_to_process:
        status = _process_single_file(file_path, ops, replace, skip_same)
        if status == "processed":
            processed_count += 1
        elif status == "no_change":
            no_change_count += 1
        else:
            skipped_count += 1

    console.print(
        f"\n[bold green]Completed:[/ ] Processed {len(files_to_process)} files.\n"
        f"- Success: {processed_count}\n"
        f"- No Change: {no_change_count}\n"
        f"- Skipped: {skipped_count}"
    )
