from openai import OpenAI
from typing import Optional
from typer import Typer
from typer import Argument
from typing_extensions import Annotated
from rich.console import Console
from rich.markdown import Markdown
from rich import print as rprint

import sqlite3
from uuid import uuid4
import asyncio
import os

from .get_data import initialize_db
from .get_data import get_sessions
from .get_data import create_session

app = Typer()
client = OpenAI()

console = Console()


home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")


@app.command()
def main(prompt: Annotated[Optional[str], Argument()] = None):

    initialize_db()
    if prompt is None:
        sessions = get_sessions()

        # Print all sessions properly
        rprint("[bold green]Saved Sessions[bold green/]")
        sessions = sessions.__reversed__()
        for session in sessions:
            rprint(f"[bold red]{session['id']}[bold red/]: ", end="")
            rprint(f"{session['title']}")
        return

    uuid = str(uuid4())[:8]
    respuesta = asyncio.run(create_session(prompt, uuid))

    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {
    #           "role": "user",
    #           "content": [
    #               {
    #                   "type": "text",
    #                   "text": f"{prompt}"
    #               }
    #           ]
    #         }
    #     ],
    #     temperature=1,
    #     max_tokens=1024,
    #     top_p=1,
    #     frequency_penalty=0,
    #     presence_penalty=0
    # )
    # # md = Markdown(response.choices[0].message.content)
    # # console.print(md)
    # print(response)


if __name__ == "__main__":
    app()
