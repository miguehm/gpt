import os
import logging
import sqlite3
import asyncio
from uuid import uuid4

# from rich import print as rprint
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown
from openai import AsyncOpenAI

from tinydb import TinyDB, Query

logging.basicConfig(level=logging.INFO)

home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")
config_path = os.path.join(data_path, "config.json")

client = AsyncOpenAI()
console = Console(width=79)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


def initialize_db():
    # Check if .terminal-gpt directory exists

    # TODO:
    # [x] Initial configuration query
    initial_query = """
    CREATE TABLE IF NOT EXISTS session (
      id TEXT PRIMARY KEY NOT NULL,
      title TEXT
    );

    CREATE TABLE IF NOT EXISTS chat (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL REFERENCES session(id),
      role TEXT NOT NULL,
      content TEXT NOT NULL
    );
    """

    system_message = """
    Eres un asistente responde solo lo referente al prompt,
    omite los saludos o despedidas.
    Cuando respondas, deberas devolver un texto de la siquiente manera:

    <Titulo> El titulo de la respuesta

    <Tu respuesta> La respuesta a enviar

    Omite los <> que escribí y su interior, recuerda que es solo para señalarte
    la estructura, no los incluyas en tu respuesta.
    En la parte del <Titulo> no incluyas estilos markdown, solo el
    texto plano
    """

    if not os.path.exists(data_path):
        logging.info("Data directory not found. Creating data directory...")
        os.makedirs(data_path)
    else:
        logging.info("Data directory has been created")

    # check if database.db exists
    if not os.path.exists(db_path):
        logging.info("Database not found. Creating database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(initial_query)
        conn.commit()
        conn.close()
        logging.info("Database created successfully.")
    else:
        logging.info("Database file has been created")

    if not os.path.exists(config_path):
        logging.info("Configuration not found. Creating json file...")

        config = TinyDB(config_path)

        config_table = config.table('configuration')

        config_table.insert({
            'app_name': 'gpt',
            'temperature': '1',
            'num_tokens': '1024',
            'top_p': '0',
            'frecuency_penalty': '0',
            'presence_penalty': '0',
            'stream': 'True',
            'model': 'gpt-4o-mini',
            'system_message': system_message,
            'actual_session': ''})
        logging.info("Configuration file created successfully")
    else:
        logging.info("Configuration file has been created")


def get_sessions() -> dict:
    # initialize_db()
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all sessions as a dictionary
    cursor.execute("SELECT * FROM session")
    sessions = cursor.fetchall()
    sessions = [{"id": session[0], "title": session[1]}
                for session in sessions]
    return sessions


async def send_prompt(messages: list, table_data: dict):
    model = table_data['model']
    temperature = float(table_data['temperature'])
    max_tokens = int(table_data['num_tokens'])
    top_p = float(table_data['top_p'])
    frequency_penalty = float(table_data['frecuency_penalty'])
    presence_penalty = float(table_data['presence_penalty'])
    stream = bool(table_data['stream'])

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stream=stream
    )

    result = ""
    with Live(Markdown(result),
              console=console,
              refresh_per_second=10) as live:
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                result += chunk.choices[0].delta.content
                live.update(Markdown(result))

    return result


def insert_to_chat(session_id: str, role: str, message: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat (session_id, role, content) VALUES (?, ?, ?)",
        (session_id,
         role,
         message
         ))
    conn.commit()
    conn.close()


def insert_session_id(id: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO session (id) VALUES (?)",
        (id,
         ))
    conn.commit()
    conn.close()


def set_session_title(id: str, title: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE session SET title = ? WHERE id = ?",
        (title,
         id
         ))
    conn.commit()
    conn.close()


async def new_session(prompt: str, session_id: str):

    # create session in database
    insert_session_id(session_id)

    # config file
    config = TinyDB(config_path)
    config_table = config.table('configuration')
    config_table_search = config_table.search(
        Query().app_name == 'gpt')
    table_data = config_table_search[0]
    system_message = table_data['system_message']

    messages = []

    initial_sys_message = {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": system_message
            }
        ]
    }
    messages.append(initial_sys_message)

    initial_user_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": prompt
            }
        ]
    }
    messages.append(initial_user_message)

    try:
        result = await send_prompt(messages, table_data)
    except Exception as e:
        print(e)
        return None

    # get the first line of a string
    title = result.split("\n")[0]

    set_session_title(session_id, title)

    # remove the firsts two lines of a string
    result = "\n".join(result.split("\n")[2:])

    # update actual session
    config_table.update({'actual_session': session_id},
                        Query().app_name == 'gpt')

    insert_to_chat(session_id,
                   "system",
                   initial_sys_message["content"][0]["text"])
    insert_to_chat(session_id,
                   "user",
                   initial_user_message["content"][0]["text"])
    insert_to_chat(session_id,
                   "assistant",
                   result)

    # return messages

if __name__ == "__main__":
    initialize_db()
    # sessions = get_sessions()

    # # Print all sessions properly
    # rprint("[bold blue]Saved Sessions[bold blue/]")
    # for session in sessions:
    #     print(f"{session['id']}: {session['title']}")

    uuid = str(uuid4())[:8]
    respuesta = asyncio.run(new_session(
        "Tipos de dato en rust",
        uuid))

    # print(respuesta)
