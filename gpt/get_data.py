import os
import logging
import sqlite3
from rich import print as rprint

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


if __name__ == "__main__":
    sessions = get_sessions()
    # rprint("[italic red]Hello[/italic red] World!")

    # Print all sessions properly
    rprint("Saved Sessions:")
    for session in sessions:
        print(f"{session['id']}: {session['title']}")
