from openai import OpenAI
from typing import Optional
from typer import Typer
from typer import Argument
from typing_extensions import Annotated
# from rich.console import Console
# from rich.markdown import Markdown
from rich import print as rprint

# import sqlite3
from uuid import uuid4
import asyncio
import os
# import sys

from .get_data import initialize_db
from .get_data import get_sessions
from .get_data import create_session
from .selector import option_panel

app = Typer()
client = OpenAI()

# console = Console()


home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")


@app.command()
def send(prompt: Annotated[Optional[str], Argument()] = None):

    initialize_db()
    uuid = str(uuid4())[:8]

    # TODO:
    # - create_session return is necessary?
    respuesta = asyncio.run(create_session(prompt, uuid))


# TODO:
# - gpt send --new : flag for new sessions?
@app.command()
def select():
    initialize_db()

    sessions = get_sessions()

    rprint("[bold green]Sessions[bold green/]")

    sessions.reverse()

    session_name = [session['title'] for session in sessions]

    selection = option_panel(session_name)

    msg = f"Actual Session: [italic blue]{
        sessions[selection]['title']}[italic blue/]"

    rprint(f"{msg}" + ' ' * (79 - len(msg) if 79 - len(msg) > 0 else 0))

    # TODO:
    # - Edit row of global config database in
    # configuration.actual_session column to remember actual session.


if __name__ == "__main__":
    app()
