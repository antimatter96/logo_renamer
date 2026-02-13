import os
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from src.shared.image_ops import ImageValidationError, load_and_validate_image

from . import genai_client, openai_client
from .image_ops import determine_new_path, get_mime_type, rename_image

console = Console()


def rename(
    image_paths: list[Path] = typer.Argument(
        ..., help="Path to the logo image file(s) or directories."
    ),
    model_name: str = typer.Option(None, help="Model to use. Defaults based on provider."),
    provider: str = typer.Option(
        "gemini", "--provider", "-p", help="AI provider: 'gemini' or 'local'."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would happen without renaming."
    ),
    max_images: int = typer.Option(
        None, "--max-images", "-n", help="Maximum number of images to process."
    ),
):
    """
    Identifies a company from its logo and renames the file to the company name.
    """
    # 0. Set Defaults
    if model_name is None:
        if provider == "gemini":
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
        else:
            model_name = os.getenv("LOCAL_OPENAI_MODEL_NAME", None)
            if not model_name:
                console.print(
                    "[bold red]Error:[/ ] LOCAL_OPENAI_MODEL_NAME not found in environment or .env file."
                )
                raise typer.Exit(code=1)

    # 1. Initialize Client
    client = None
    if provider == "gemini":
        client = genai_client.get_client()
        if not client:
            console.print(
                "[bold red]Error:[/ ] GEMINI_API_KEY not found in environment or .env file."
            )
            console.print(
                "Please set your API key in a .env file: [bold]GEMINI_API_KEY=your_key_here[/]"
            )
            raise typer.Exit(code=1)
    elif provider == "local":
        client = openai_client.get_client()
        # Local client usually doesn't fail on init, but we check anyway if needed
    else:
        console.print(
            f"[bold red]Error:[/ ] Unknown provider '{provider}'. Use 'gemini' or 'local'."
        )
        raise typer.Exit(code=1)

    # 2. Collect Files
    files_to_process = []
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

    for path in image_paths:
        if path.is_dir():
            dir_files = [
                (p, path / "renamed")
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
            files_to_process.append((path, None))

    if not files_to_process:
        console.print("[bold yellow]Warning:[/ ] No image files found to process.")
        return

    total_found = len(files_to_process)
    if max_images is not None and max_images > 0 and max_images < total_found:
        files_to_process = files_to_process[:max_images]
        console.print(
            f"[bold blue]Bulk Processing:[/ ] Found {total_found} images, but renaming only {len(files_to_process)}"
        )
    elif len(image_paths) == 1 and image_paths[0].is_dir():
        console.print(
            f"[bold blue]Bulk Processing:[/ ] Found {len(files_to_process)} images in {image_paths[0]}"
        )
    elif len(files_to_process) > 1:
        console.print(f"[bold blue]Processing {len(files_to_process)} image(s)...[/ ]")

    # 3. Process Files
    success_count = 0
    for i, (file_path, target_dir) in enumerate(files_to_process):
        # Rate limit for Gemini to avoid hitting API limits
        if provider == "gemini" and i > 0:
            time.sleep(11)

        try:
            if _process_single_file(
                client, file_path, model_name, provider, dry_run, target_dir=target_dir
            ):
                success_count += 1
        except Exception as e:
            console.print(f"[bold red]Error processing {file_path.name}:[/ ] {e}")

    console.print(
        f"\n[bold green]Completed:[/ ] Processed {len(files_to_process)} files. {success_count} renamed successfully."
    )


def _process_single_file(
    client,
    image_path: Path,
    model_name: str,
    provider: str,
    dry_run: bool,
    target_dir: Path = None,
) -> bool:
    """
    Processes a single image file: validation, identification, and renaming.
    Returns True if successful (renamed or correctly named), False otherwise.
    """
    # 2. Validate and Load Image
    try:
        image_bytes = load_and_validate_image(image_path)
    except ImageValidationError as e:
        console.print(f"[bold red]Skip {image_path.name}:[/ ] {e}")
        return False

    mime_type = get_mime_type(image_path)

    # 3. Identify Company
    console.print(
        f"[bold blue]Processing:[/ ] {image_path.name} using [red]{provider}[/]/[magenta]{model_name}[/]"
    )
    try:
        if provider == "gemini":
            company_name = genai_client.identify_company(
                client=client,
                image_bytes=image_bytes,
                mime_type=mime_type,
                model_name=model_name,
            )
        else:
            company_name = openai_client.identify_company(
                client=client,
                image_bytes=image_bytes,
                mime_type=mime_type,
                model_name=model_name,
            )
    except Exception as e:
        console.print(f"[bold red]Error identifying {image_path.name}:[/ ] {e}")
        return False

    if not company_name:
        console.print(
            f"[bold yellow]Warning:[/ ] Could not identify a company name for {image_path.name}."
        )
        return False

    # 4. Determine New Path
    new_path = determine_new_path(image_path, company_name, target_dir=target_dir)
    new_filename = new_path.name

    if image_path.absolute() == new_path.absolute():
        console.print(f"[bold green]Already named correctly:[/ ] {image_path.name}")
        return True

    # 5. Execute or Dry Run
    if dry_run:
        dest_desc = f"{new_path.parent.name}/{new_filename}" if target_dir else new_filename
        console.print(
            Panel(
                f"Dry Run: [bold cyan]{image_path.name}[/] -> [bold green]{dest_desc}[/]",
                title="Proposed Change",
            )
        )
        return True
    else:
        try:
            final_path = rename_image(image_path, new_path)

            # Check if we had to handle a collision
            if final_path.name != new_filename:
                console.print(
                    "[bold yellow]Collision:[/ ] Name already exists. Appending timestamp."
                )

            dest_display = (
                f"{final_path.parent.name}/{final_path.name}" if target_dir else final_path.name
            )
            console.print(
                f"[bold green]Renamed:[/ ] [bold cyan]{image_path.name}[/] -> [bold green]{dest_display}[/]"
            )
            return True

        except FileExistsError as e:
            console.print(f"[bold red]Error renaming {image_path.name}:[/ ] {e}. Skipping.")
            return False
        except Exception as e:
            console.print(f"[bold red]Error renaming {image_path.name}:[/ ] {e}")
            return False
