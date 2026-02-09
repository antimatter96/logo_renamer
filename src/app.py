import typer
from rich.console import Console

from src.commands.rename.cli import rename
from src.commands.trim.cli import trim
from src.commands.extend.cli import extend

app = typer.Typer(help="Logo Renamer: Identify and trim company logos.")
console = Console()

app.command()(rename)
app.command()(trim)
app.command()(extend)
