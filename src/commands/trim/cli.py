from pathlib import Path

import typer
from rich.console import Console

from .image_ops import trim_image

console = Console()


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
