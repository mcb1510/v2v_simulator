import os
import sqlite3
import time

# Ensure absolute path to the database file
PROJECT_ROOT: str = os.path.dirname(os.path.abspath(__file__))

# Log file name with unique timestamp
CURRENT_TIME: str = time.strftime("%Y%m%d_%H%M%S")
DB_PATH: str = os.path.join(PROJECT_ROOT, f"logs_{CURRENT_TIME}.db")
INIT_DB_SCRIPT: str = os.path.join(os.path.dirname(__file__), "init_db.sql")

def _db_connection() -> sqlite3.Connection:
  """Gets a connection to the sqlite3 database.
  
  Returns:
    sqlite3.Connection: A connection to the sqlite3 database.
  """

  db: sqlite3.Connection = sqlite3.connect(DB_PATH)
  db.execute("PRAGMA foreign_keys = ON;")
  return db

def init_logging() -> None:
  """Initializes a new database for logs.

  The database is created with the current timestamp as part of the name,
  and it uses the `init_db.sql` script to initialize the database.
  """

  if not os.path.exists(DB_PATH):
    print("Creating new database...")
    db: sqlite3.Connection = _db_connection()
    db_cursor: sqlite3.Cursor = db.cursor()
    with open(INIT_DB_SCRIPT, 'r') as init_script:
      db_cursor.executescript(init_script.read())

    db.commit()
    db.close()
    print("Database created!")
  else:
    print("Using existing database")

def _add_log(message_type: str, message: str) -> None:
  """Adds a message with the message type to the log database.
  
  Args:
    message_type (str): The type of the message (INFO, WARNING, ERROR).
    message (str): The message for the log.
  """

  db: sqlite3.Connection = _db_connection()
  db_cursor: sqlite3.Cursor = db.cursor()

  try:
    columns: list[str] = ["MESSAGE_TYPE", "MESSAGE"]
    values: list[object] = [message_type, message]

    # Construct the query. In this case, it will look like this:
    # INSERT INTO LOGS (MESSAGE_TYPE, MESSAGE) VALUES (?, ?)
    query: str = f"INSERT INTO LOGS ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"

    # Then put the actual values into the query. This method
    # is safe from SQL injection attacks.
    db_cursor.execute(query, values)
    db.commit()

  except sqlite3.IntegrityError as e:
    print(e)

  finally:
    db.close()

def log_info(message: str):
  """Adds an info log to the database.
  
  Args
    message (str): The message for the log.
  """

  _add_log("INFO", message)

def log_warning(message: str):
  """Adds a warning log to the database.
  
  Args
    message (str): The message for the log.
  """

  _add_log("WARNING", message)

def log_error(message: str):
  """Adds an error log to the database.
  
  Args
    message (str): The message for the log.
  """

  _add_log("ERROR", message)

__all__ = ["init_logging", "log_info", "log_warning", "log_error"]
