from pathlib import Path

import typer
from rich.console import Console

from src.shared.image_ops import ImageValidationError, load_and_validate_image

from .image_ops import trim_image

console = Console()


def trim(
    image_paths: list[Path] = typer.Argument(
        ..., help="Path to the image file(s) or directories."
    ),
    margin: int = typer.Option(48, help="Margin in pixels to leave around the content."),
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
    # 1. Collect Files
    files_to_process = []
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

    for path in image_paths:
        if path.is_dir():
            dir_files = [
                p
                for p in path.iterdir()
                if p.is_file() and p.suffix.lower() in valid_extensions
            ]
            if not dir_files:
                console.print(f"[bold yellow]Warning:[/ ] No image files found in {path}")
                continue
            files_to_process.extend(dir_files)
        else:
            if not path.exists():
                console.print(f"[bold red]Error:[/ ] File not found: {path}")
                continue
            files_to_process.append(path)

    if not files_to_process:
        console.print("[bold yellow]Warning:[/ ] No image files found to process.")
        return

    if len(image_paths) == 1 and image_paths[0].is_dir():
        console.print(
            f"[bold blue]Bulk Trimming:[/ ] Found {len(files_to_process)} images in {image_paths[0]}"
        )
    elif len(files_to_process) > 1:
        console.print(f"[bold blue]Trimming {len(files_to_process)} image(s)...[/ ]")

    # 2. Process Files
    trimmed_count = 0
    no_change_count = 0
    skipped_count = 0

    for file_path in files_to_process:
        try:
            status = _process_single_file(file_path, margin, replace)
            if status == "trimmed":
                trimmed_count += 1
            elif status == "no_change":
                no_change_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            console.print(f"[bold red]Error processing {file_path.name}:[/ ] {e}")
            skipped_count += 1

    console.print(
        f"\n[bold green]Completed:[/ ] Processed {len(files_to_process)} files.\n"
        f"- Trimmed: {trimmed_count}\n"
        f"- No Change: {no_change_count}\n"
        f"- Skipped: {skipped_count}"
    )


def _process_single_file(image_path: Path, margin: int, replace: bool) -> str:
    """
    Processes a single image file: validation and trimming.
    Returns status: 'trimmed', 'no_change', or 'skipped'.
    """
    try:
        # 1. Validate image
        load_and_validate_image(image_path)
    except ImageValidationError as e:
        console.print(f"[bold red]Skip {image_path.name}:[/ ] {e}")
        return "skipped"

    # 2. Trim image
    try:
        output_path, was_modified = trim_image(image_path, margin, replace)
        if not was_modified:
            console.print(
                f"[bold yellow]Warning:[/ ] No changes for {image_path.name} (already optimal size)"
            )
            return "no_change"
        console.print(f"[bold green]Trimmed:[/ ] {image_path.name} -> {output_path.name}")
        return "trimmed"
    except ImageValidationError as e:
        console.print(f"[bold red]Skip {image_path.name}:[/ ] {e}")
        return "skipped"
    except Exception as e:
        console.print(f"[bold red]Error trimming {image_path.name}:[/ ] {e}")
        return "skipped"
