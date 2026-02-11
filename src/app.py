import typer
from rich.console import Console

from src.commands.manipulate.cli import manipulate
from src.commands.rename.cli import rename

app = typer.Typer(help="Logo Renamer: Identify and trim company logos.")
console = Console()

app.command()(rename)
app.command(name="manipulate")(manipulate)
