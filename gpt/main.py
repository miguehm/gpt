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
import logging

from .get_data import initialize_db
from .get_data import get_sessions
from .get_data import new_session
from .get_data import cont_session
from .get_data import get_config_data
from .get_data import update_config_data
from .get_data import check_log
from .get_data import print_history
from .get_data import show_config
from .get_data import delete_session
from .selector import option_panel

app = Typer()
client = OpenAI()

home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")
config_path = os.path.join(data_path, "config.json")

initialize_db()

if os.path.exists(db_path):
    check_log()


@app.command()
def new(prompt: Annotated[Optional[str], Argument()] = None) -> None:
    """
    gpt new "[PROMPT]"
    - Begin a new conversation
    """

    uuid: str = str(uuid4())[:8]

    asyncio.run(new_session(prompt, uuid))


@app.command()
def cont(prompt: Annotated[Optional[str], Argument()] = None):
    """
    gpt cont "[PROMPT]"
    - Continue ACTUAL SESSION conversation
    """
    # initialize_db()

    config = TinyDB(config_path)
    config_table = config.table('configuration')
    query_table = config_table.search(Query().app_name == 'gpt')
    table: dict = query_table[0]
    actual_session_uuid: str = table['actual_session']
    if actual_session_uuid == "":
        rprint("[bold blue]You don't created any session yet.[bold blue/]")
        rprint("""
            Begin a new session using:
            \t[italic]gpt new '[PROMPT]'[italic/]
            """)
        return
    # print(actual_session_uuid)
    asyncio.run(cont_session(prompt, actual_session_uuid))


@app.command()
def select():
    """
    gpt select
    - Select an ACTUAL SESSION for continue conversation
    """
    # initialize_db()

    sessions = get_sessions()

    rprint("[bold green]Sessions[bold green/]")

    if sessions.__len__() == 0:
        rprint("[bold blue]You don't created any session yet.[bold blue/]")
        rprint("""
            Begin a new session using:
            \t[italic]gpt new '[PROMPT]'[italic/]
            """)
        return

    # The most recent first
    sessions.reverse()

    # print session panel
    sessions_name: list = [session['title'] for session in sessions]
    selection: int = option_panel(sessions_name)

    # getting data from choice
    title: str = sessions[selection]['title']
    id: str = sessions[selection]['id']

    # Update actual session
    config = TinyDB(config_path)
    config_table = config.table('configuration')
    config_table.update({'actual_session': id},
                        Query().app_name == 'gpt')

    # Clear and print title selected choice
    msg: str = f"Actual Session: [italic blue]{title}[italic blue/]"
    sys.stdout.write(' ' * 79 + "\n")
    sys.stdout.flush()
    sys.stdout.write('\033[A' * 1)
    rprint(f'{msg}')


@app.command()
def log():
    """
    gpt log - Toggle log mode
    """
    table: dict = get_config_data(config_path)
    log_status: bool = table['log']

    if log_status:
        update_config_data(config_path, {'log': 'False'})
        rprint("Log mode [bold red]False[bold red/]")
    else:
        update_config_data(config_path, {'log': 'True'})
        rprint("Log mode [bold green]True[bold green/]")


@app.command()
def history():
    """
    gpt history - Show message history of actual session
    """
    table: dict = get_config_data(config_path)
    actual_session_uuid: str = str(table['actual_session'])

    print_history(actual_session_uuid)


@app.command()
def config():
    """
    gpt config - Print values of configuration file
    """
    rprint("[bold green]Configuration[/]")
    show_config()


@app.command()
def delete():
    """
    gpt delete - Delete a session
    """

    delete_session()


if __name__ == "__main__":
    app()
