from openai import OpenAI
from typer import Typer
from rich.console import Console
from rich.markdown import Markdown
from rich import print as rprint

import sqlite3

from .get_data import get_sessions

app = Typer()
client = OpenAI()

console = Console()


@app.command()
def main(prompt: str = ""):

    if prompt == "":
        sessions = get_sessions()

        # Print all sessions properly
        rprint("[bold green]Saved Sessions[bold green/]")
        for session in sessions:
            print(f"[bold red]{session['id']}[bold red/]: {session['title']}")
        return

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
              "role": "user",
              "content": [
                  {
                      "type": "text",
                      "text": f"{prompt}"
                  }
              ]
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    md = Markdown(response.choices[0].message.content)
    console.print(md)


if __name__ == "__main__":
    app()
