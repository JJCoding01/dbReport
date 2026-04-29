# pylint: disable=duplicate-code

import sqlite3

from pathlib import Path


def extract_triggers(conn: sqlite3.Connection):
    """
    Extract all triggers from the database

    Parameters:
        conn: sqlite3.Connection
            connection to database

    Returns:
        dict: dictionary in the form `{trigger_name: trigger_sql}`
    """

    cursor = conn.cursor()
    search_sql = r'SELECT name, sql FROM sqlite_master WHERE type = "trigger"'

    # Extract the trigger sql. Keep the CREATE TRIGGER ... text
    results = {r[0]: r[1] for r in cursor.execute(search_sql).fetchall()}

    cursor.close()
    return results


def update_triggers(conn: sqlite3.Connection, triggers: dict, exist_ok=True):
    """
    Updates triggers

    Parameters:
        conn: sqlite3.Connection
            connection to database
        triggers: dict
            details of trigger to update in the form {trigger_name: trigger_sql}
        exist_ok: bool (default True)
            whether to update existing trigger or raise exception if trigger exists
    """

    cursor = conn.cursor()

    for trigger_name, sql in triggers.items():
        if exist_ok:
            # delete existing trigger if it exists, and then recreate it
            cursor.execute(f"DROP TRIGGER IF EXISTS '{trigger_name}'")

        cursor.execute(sql)

    cursor.close()


def export_triggers(save_dir: Path, db_path: Path):
    """
    Export all triggers from a database to individual SQL files

    Parameters:
        save_dir: Path
            directory where SQL files will be written
        db_path: Path
            path to the SQLite database file
    """

    conn = sqlite3.connect(db_path)
    triggers = extract_triggers(conn)
    conn.close()

    for trigger, sql in triggers.items():
        (save_dir / f"{trigger}.sql").write_text(sql, encoding="utf-8")


def import_triggers(path: Path, db_path: Path):
    """
    Import triggers from SQL files into the database

    Parameters:
        path: Path
            directory containing `.sql` files to import, or a single `.sql` file
            (the trigger name is taken from the file stem)
        db_path: Path
            path to the SQLite database file
    """

    conn = sqlite3.connect(db_path)

    if path.is_dir():
        triggers = {
            f.stem: f.read_text(encoding="utf-8")
            for f in path.iterdir()
            if f.is_file() and f.suffix == ".sql"
        }
    else:
        triggers = {path.stem: path.read_text(encoding="utf-8")}

    update_triggers(conn, triggers, exist_ok=True)
    conn.close()
