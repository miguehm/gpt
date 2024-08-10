from openai import OpenAI
from typing import Optional
from typer import Typer
from typer import Argument
from typing_extensions import Annotated
from tinydb import TinyDB, Query
from rich import print as rprint

# import sqlite3
from uuid import uuid4
import asyncio
import os
import sys

from .get_data import initialize_db
from .get_data import get_sessions
from .get_data import new_session
from .selector import option_panel

app = Typer()
client = OpenAI()

# console = Console()

home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")
config_path = os.path.join(data_path, "config.json")


@app.command()
def new(prompt: Annotated[Optional[str], Argument()] = None):

    initialize_db()
    uuid = str(uuid4())[:8]

    # TODO:
    # - create_session return is necessary?
    respuesta = asyncio.run(new_session(prompt, uuid))


# TODO:
# - [x] gpt new: from `gpt select`. Creates new session
# - [ ] gpt cont: Continue conversation based on actual_session config variable
@app.command()
def select():
    initialize_db()

    sessions = get_sessions()

    rprint("[bold green]Sessions[bold green/]")

    sessions.reverse()

    session_name = [session['title'] for session in sessions]

    selection = option_panel(session_name)

    title = sessions[selection]['title']
    id = sessions[selection]['id']

    config = TinyDB(config_path)
    config_table = config.table('configuration')
    config_table.update({'actual_session': id},
                        Query().app_name == 'gpt')

    msg = f"Actual Session: [italic blue]{title}[italic blue/]"

    sys.stdout.write(' ' * 79 + "\n")
    sys.stdout.flush()
    sys.stdout.write('\033[A' * 1)
    rprint(f'{msg}')


if __name__ == "__main__":
    app()
