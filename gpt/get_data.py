import os
import logging
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown
from openai import AsyncOpenAI
import sqlite3
from tinydb import TinyDB, Query

logging.basicConfig(level=logging.INFO)

# directories
home_dir = os.path.expanduser("~/.config/")
data_path = os.path.join(home_dir, "terminal-gpt")
db_path = os.path.join(data_path, "database.db")
config_path = os.path.join(data_path, "config.json")

client = AsyncOpenAI()
console = Console(width=79)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


def initialize_db() -> None:
    """
    Initialize chat database and configuration file
    """

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
    En la primera linea incluiras el titulo del prompt (no incluyas
    estilos markdown), despues dejarás una linea en blanco y
    escribiras el prompt que ibas a enviar desde el principio.
    
    Responde brevemente y de forma concisa, sin embago, si y solo si el usuario
    te pide una explicación detallada, hazlo, y despues continua siendo
    breve y conciso.
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

        # default conf
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


def get_sessions() -> list:
    # Connect to database
    logging.info("Getting sessions from database")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all sessions as a dictionary
    cursor.execute("SELECT * FROM session")
    sessions = cursor.fetchall()
    sessions = [{"id": session[0], "title": session[1]}
                for session in sessions]
    return sessions


async def send_prompt(messages: list, table_data: dict) -> str:
    """
    Send a promt in stream mode as default
    """

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


def insert_to_chat(session_id: str, role: str, message: str) -> None:
    """
    Insert a message to chat table in database
    """

    logging.info("Inserting message to chat table in database")
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


def insert_session_id(id: str) -> None:
    """
    Insert new session id to session table in database
    """

    logging.info("Inserting session_id to session table in database")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO session (id) VALUES (?)",
        (id,
         ))
    conn.commit()
    conn.close()


def set_session_title(id: str, title: str) -> None:
    """
    Insert title to session table in database
    """
    logging.info("Inserting title to session table in database")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE session SET title = ? WHERE id = ?",
        (title,
         id
         ))
    conn.commit()
    conn.close()


def get_config_data(config_path) -> dict:
    """
    Get configuration data from config.json file
    """

    logging.info("Getting configuration data")
    config = TinyDB(config_path)
    config_table = config.table('configuration')
    config_table_search = config_table.search(
        Query().app_name == 'gpt')
    table_data: dict = config_table_search[0]
    return table_data


def update_config_data(config_path, data: dict) -> None:
    """
    Update configuration data from config.json file
    """

    logging.info("Updating configuration data")
    config = TinyDB(config_path)
    config_table = config.table('configuration')
    config_table.update(data,
                        Query().app_name == 'gpt')


def json_message(role: str, content: str) -> dict:
    """
    Return a dict with base structure of a OpenAI API message
    """

    message = {
        "role": role,
        "content": [
            {
                "type": "text",
                "text": content
            }
        ]
    }
    return message


async def new_session(prompt: str, session_id: str) -> None:
    """
    Create a new session/conversation
    """

    # create session in database
    insert_session_id(session_id)

    table_data = get_config_data(config_path)
    system_message = table_data['system_message']

    messages = []

    initial_sys_message = json_message('system', system_message)
    messages.append(initial_sys_message)

    initial_user_message = json_message('user', prompt)
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

    # update actual session in configurations
    update_config_data(config_path, {'actual_session': session_id})

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


def get_chat(session_id: str) -> list:
    """
    Get session history from db using the session_id
    and return a dict list of session history
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # select role, content from chat where session_id = session_id
    cursor.execute("SELECT role, content FROM chat WHERE session_id = ?",
                   (session_id,))
    chat = cursor.fetchall()

    # print(chat)
    messages: list = []

    for message in chat:
        role = message[0]
        content = message[1]
        base_message: dict = json_message(role, content)
        messages.append(base_message)

    return messages


async def cont_session(prompt: str, session_id: str):

    messages: list = get_chat(session_id)

    user_message: dict = json_message('user', prompt)
    messages.append(user_message)

    table_data: dict = get_config_data(config_path)
    try:
        result = await send_prompt(messages, table_data)
    except Exception as e:
        print(e)
        return None

    insert_to_chat(session_id, "assistant", result)


if __name__ == "__main__":
    initialize_db()
    # sessions = get_sessions()

    # # Print all sessions properly
    # rprint("[bold blue]Saved Sessions[bold blue/]")
    # for session in sessions:
    #     print(f"{session['id']}: {session['title']}")

    # uuid = str(uuid4())[:8]
    # respuesta = asyncio.run(new_session(
    #     "Tipos de dato en rust",
    #     uuid))

    # print(respuesta)

    # get_chat('ad374613')
