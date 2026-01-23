from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

import genai_client
import image_ops

# Load environment variables
load_dotenv()

app = typer.Typer(help="Rename company logos based on brand recognition.")
console = Console()


@app.command()
def rename(
    image_path: Path = typer.Argument(..., help="Path to the logo image file."),
    model_name: str = typer.Option("gemini-3-flash-preview", help="Gemini model to use."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would happen without renaming."
    ),
):
    """
    Identifies a company from its logo and renames the file to the company name.
    """
    # 1. Initialize Client
    client = genai_client.get_client()
    if not client:
        console.print(
            "[bold red]Error:[/] GEMINI_API_KEY not found in environment or .env file."
        )
        console.print(
            "Please set your API key in a .env file: [bold]GEMINI_API_KEY=your_key_here[/]"
        )
        raise typer.Exit(code=1)

    # 2. Validate and Load Image
    try:
        image_bytes = image_ops.load_and_validate_image(image_path)
    except image_ops.ImageValidationError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)

    mime_type = image_ops.get_mime_type(image_path)

    # 3. Identify Company
    console.print(f"[bold blue]Processing:[/] {image_path.name}...")
    try:
        company_name = genai_client.identify_company(
            client=client, image_bytes=image_bytes, mime_type=mime_type, model_name=model_name
        )
    except Exception as e:
        console.print(f"[bold red]Error during API call:[/] {e}")
        raise typer.Exit(code=1)

    if not company_name:
        console.print("[bold yellow]Warning:[/] Could not identify a company name.")
        return

    # 4. Determine New Path
    new_path = image_ops.determine_new_path(image_path, company_name)
    new_filename = new_path.name

    if image_path.name == new_filename:
        console.print(f"[bold green]Already named correctly:[/] {image_path.name}")
        return

    # 5. Execute or Dry Run
    if dry_run:
        console.print(
            Panel(
                f"Dry Run: [bold cyan]{image_path.name}[/] -> [bold green]{new_filename}[/]",
                title="Proposed Change",
            )
        )
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

        except FileExistsError as e:
            console.print(f"[bold red]Error:[/] {e}. Skipping.")
        except Exception as e:
            console.print(f"[bold red]Error during rename:[/] {e}")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
