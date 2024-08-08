import os
import logging
import sqlite3
import asyncio
from uuid import uuid4

from rich import print as rprint
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)

initial_query = """
CREATE TABLE IF NOT EXISTS session (
  id TEXT PRIMARY KEY NOT NULL,
  title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES session(id),
  role TEXT NOT NULL,
  content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS configuration (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES session(id),
  temperature FLOAT NOT NULL,
  max_tokens INT NOT NULL,
  top_p FLOAT NOT NULL,
  frequency_penalty FLOAT NOT NULL,
  presence_penalty FLOAT NOT NULL
);
"""

home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")

client = AsyncOpenAI()
console = Console(width=79)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


def initialize_db():
    # Check if .terminal-gpt directory exists
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


def get_sessions() -> dict:
    initialize_db()
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all sessions as a dictionary
    cursor.execute("SELECT * FROM session")
    sessions = cursor.fetchall()
    sessions = [{"id": session[0], "title": session[1]}
                for session in sessions]
    return sessions


"""
ChatCompletion(id='chatcmpl-9tlWjJZDCdKHNlzvv9Yjl8CzSZVC4', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessag
e(content='Hola, ¿cómo estás? ¿En qué puedo ayudarte hoy?', refusal=None, role='assistant', function_call=None, tool_calls=None))], created=1723077761
, model='gpt-4o-2024-05-13', object='chat.completion', service_tier=None, system_fingerprint='fp_c9aa9c0491', usage=CompletionUsage(completion_tokens=
13, prompt_tokens=8, total_tokens=21))
"""


async def send_prompt(messages: list):
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
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


async def create_session(prompt: str, session_id: str):

    # create session in database

    messages = []

    initial_sys_message = {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "Eres un asistente que habla de forma breve y concisa"
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
        result = await send_prompt(messages)
    except Exception as e:
        print(e)
        return None

    # json_result = {
    #     "role": "assistant",
    #     "content": [
    #         {
    #             "type": "text",
    #             "text": result
    #         }
    #     ]
    # }
    #
    # messages.append(json_result)

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
    # sessions = get_sessions()
    #
    # # Print all sessions properly
    # rprint("Saved Sessions:")
    # for session in sessions:
    #     print(f"{session['id']}: {session['title']}")

    uuid = str(uuid4())[:8]
    respuesta = asyncio.run(create_session(
        "Un hola mundo en javascript",
        uuid))

    # print(respuesta)
