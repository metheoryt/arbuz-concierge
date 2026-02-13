import typer
from rich.console import Console

from app.loader import load_all

app = typer.Typer(help="Arbuz Concierge CLI")
console = Console()


@app.command()
def load():
    """
    Load all categories and products from Arbuz.kz
    """
    console.print("[bold green]Starting data load...[/bold green]")
    load_all()
    console.print("[bold green]Data load completed successfully.[/bold green]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
