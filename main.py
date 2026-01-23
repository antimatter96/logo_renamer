import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from rich.console import Console
from rich.panel import Panel

# Load environment variables
load_dotenv()

app = typer.Typer(help="Rename company logos based on brand recognition.")
console = Console()

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/] GEMINI_API_KEY not found in environment or .env file.")
        console.print("Please set your API key in a .env file: [bold]GEMINI_API_KEY=your_key_here[/]")
        raise typer.Exit(code=1)
    return genai.Client(api_key=api_key)

@app.command()
def rename(
    image_path: Path = typer.Argument(..., help="Path to the logo image file."),
    model_name: str = typer.Option("gemini-3-flash-preview", help="Gemini model to use."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would happen without renaming."),
):
    """
    Identifies a company from its logo and renames the file to the company name.
    """
    if not image_path.exists():
        console.print(f"[bold red]Error:[/] File '{image_path}' does not exist.")
        raise typer.Exit(code=1)

    client = get_client()

    try:
        # Load image to verify it's valid
        img = Image.open(image_path)
        
        console.print(f"[bold blue]Processing:[/] {image_path.name}...")

        # Read image bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = (
            "Identify the company or brand in this logo image. "
            "If there is no text, identify it based on visual features (like a reverse image search). "
            "Return ONLY the company name formatted as a clean filename (lowercase, snake_case, no special characters, no file extension). "
            "Example output: 'google' or 'coca_cola' or 'nike'."
        )

        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=f"image/{image_path.suffix[1:]}"),
                prompt,
            ]
        )

        company_name = response.text.strip().lower()
        
        # Basic sanitization just in case
        company_name = "".join(c if c.isalnum() or c == "_" else "_" for c in company_name)
        
        if not company_name:
            console.print("[bold yellow]Warning:[/] Could not identify a company name.")
            return

        extension = image_path.suffix
        new_filename = f"{company_name}{extension}"
        new_path = image_path.parent / new_filename

        if image_path.name == new_filename:
            console.print(f"[bold green]Already named correctly:[/] {image_path.name}")
            return

        if dry_run:
            console.print(Panel(f"Dry Run: [bold cyan]{image_path.name}[/] -> [bold green]{new_filename}[/]", title="Proposed Change"))
        else:
            # Handle collision
            if new_path.exists():
                console.print(f"[bold yellow]Collision:[/] {new_filename} already exists. Skipping.")
                return
                
            image_path.rename(new_path)
            console.print(f"[bold green]Renamed:[/] [bold cyan]{image_path.name}[/] -> [bold green]{new_filename}[/]")

    except Exception as e:
        console.print(f"[bold red]Error during processing:[/] {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
