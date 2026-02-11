import typer
from rich.console import Console

from src.commands.rename.cli import rename
from src.commands.manipulate.cli import manipulate

app = typer.Typer(help="Logo Renamer: Identify and trim company logos.")
console = Console()

app.command()(rename)
app.command(name="manipulate")(manipulate)
# Alias for convenience if desired, but let's stick to one clear name first.
# app.command(name="process")(manipulate) 
