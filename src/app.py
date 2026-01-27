import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

import src.genai_client as genai_client
import src.image_ops as image_ops
import src.openai_client as openai_client

app = typer.Typer(help="Rename company logos based on brand recognition.")
console = Console()


@app.command()
def rename(
    image_path: Path = typer.Argument(..., help="Path to the logo image file."),
    model_name: str = typer.Option(None, help="Model to use. Defaults based on provider."),
    provider: str = typer.Option(
        "gemini", "--provider", "-p", help="AI provider: 'gemini' or 'local'."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would happen without renaming."
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
                    "[bold red]Error:[/] LOCAL_OPENAI_MODEL_NAME not found in environment or .env file."
                )
                raise typer.Exit(code=1)

    # 1. Initialize Client
    client = None
    if provider == "gemini":
        client = genai_client.get_client()
        if not client:
            console.print(
                "[bold red]Error:[/] GEMINI_API_KEY not found in environment or .env file."
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
            f"[bold red]Error:[/] Unknown provider '{provider}'. Use 'gemini' or 'local'."
        )
        raise typer.Exit(code=1)

    # 2. Process Input
    if image_path.is_dir():
        # Bulk processing
        # Filter for common image extensions to avoid trying to read everything
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
            f"[bold blue]Bulk Processing:[/] Found {len(files_to_process)} images in {image_path}"
        )

        success_count = 0
        for file_path in files_to_process:
            try:
                if _process_single_file(client, file_path, model_name, provider, dry_run):
                    success_count += 1
            except Exception as e:
                console.print(f"[bold red]Error processing {file_path.name}:[/] {e}")

        console.print(
            f"\n[bold green]Completed:[/] Processed {len(files_to_process)} files. {success_count} renamed successfully."
        )

    else:
        # Single file processing
        try:
            _process_single_file(client, image_path, model_name, provider, dry_run)
        except Exception as e:
            # For single file, we might want to re-raise to exit with error code,
            # but the helper handles printing errors.
            # If it was a critical error, the helper might have raised.
            # Let's ensure we exit with 1 if it failed.
            console.print(f"[bold red]Failed:[/] {e}")
            raise typer.Exit(code=1)


def _process_single_file(
    client, image_path: Path, model_name: str, provider: str, dry_run: bool
) -> bool:
    """
    Processes a single image file: validation, identification, and renaming.
    Returns True if successful (renamed or correctly named), False otherwise.
    """
    # 2. Validate and Load Image
    try:
        image_bytes = image_ops.load_and_validate_image(image_path)
    except image_ops.ImageValidationError as e:
        console.print(f"[bold red]Skip {image_path.name}:[/] {e}")
        return False

    mime_type = image_ops.get_mime_type(image_path)

    # 3. Identify Company
    console.print(
        f"[bold blue]Processing:[/] {image_path.name} using [red]{provider}[/]/[magenta]{model_name}[/]"
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
        console.print(f"[bold red]Error identifying {image_path.name}:[/] {e}")
        return False

    if not company_name:
        console.print(
            f"[bold yellow]Warning:[/] Could not identify a company name for {image_path.name}."
        )
        return False

    # 4. Determine New Path
    new_path = image_ops.determine_new_path(image_path, company_name)
    new_filename = new_path.name

    if image_path.name == new_filename:
        console.print(f"[bold green]Already named correctly:[/] {image_path.name}")
        return True

    # 5. Execute or Dry Run
    if dry_run:
        console.print(
            Panel(
                f"Dry Run: [bold cyan]{image_path.name}[/] -> [bold green]{new_filename}[/]",
                title="Proposed Change",
            )
        )
        return True
    else:
        try:
            final_path = image_ops.rename_image(image_path, new_path)

            # Check if we had to handle a collision
            if final_path.name != new_filename:
                console.print(
                    "[bold yellow]Collision:[/] Name already exists. Appending timestamp."
                )

            console.print(
                f"[bold green]Renamed:[/] [bold cyan]{image_path.name}[/] -> [bold green]{final_path.name}[/]"
            )
            return True

        except FileExistsError as e:
            console.print(f"[bold red]Error renaming {image_path.name}:[/] {e}. Skipping.")
            return False
        except Exception as e:
            console.print(f"[bold red]Error renaming {image_path.name}:[/] {e}")
            return False
