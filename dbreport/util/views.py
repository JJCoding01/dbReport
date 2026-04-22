# pylint: disable=duplicate-code
import re
import sqlite3

from pathlib import Path

# regex to stip out the text needed to create the view (match any quoting style)
CREATE_VIEW_RE = re.compile(
    r'^\s*CREATE\s+VIEW\s+(?:"[^"]*"|`[^`]*`|\[[^\]]*\]|\S+)\s+AS\s*',
    re.IGNORECASE,
)


def extract_views(conn: sqlite3.Connection):
    """
    Extract all views from the database

    Parameters:
        conn: sqlite3.Connection
            connection to database

    Returns:
        dict: dictionary in the form `{view_name: view_sql}`
    """

    c = conn.cursor()
    search_sql = r'SELECT name, sql FROM sqlite_master WHERE type = "view"'

    # Extract the view sql. But disregard the CREATE VIEW ... AS text
    results = {
        r[0]: CREATE_VIEW_RE.sub("", r[1], count=1)
        for r in c.execute(search_sql).fetchall()
    }

    c.close()
    return results


def update_views(conn: sqlite3.Connection, views: dict, exist_ok=True):
    """
    Updates views

    Parameters:
        conn: sqlite3.Connection
            connection to database
        views: dict
            details of view to update in the form {view_name: view_sql}
        exist_ok: bool (default True)
            whether to update existing view or raise exception if view exists
    """

    cursor = conn.cursor()

    for view_name, sql_view in views.items():
        view_name_q = f'"{view_name}"'

        if exist_ok:
            cursor.execute(f"DROP VIEW IF EXISTS {view_name_q}")

        cursor.execute(f"CREATE VIEW {view_name_q} AS {sql_view}")

    cursor.close()


def export_views(save_dir: Path, db_path: Path):
    """
    Export all views from a database to individual SQL files

    Parameters:
        save_dir: Path
            directory where SQL files will be written
        db_path: Path
            path to the SQLite database file
    """

    conn = sqlite3.connect(db_path)

    views = extract_views(conn)

    for view, sql in views.items():
        with open(save_dir / f"{view}.sql", "w", encoding="utf-8") as f:
            f.write(sql)

    conn.close()


def import_views(path: Path, db_path: Path):
    """
    Import views from SQL files into the database

    Parameters:
        path: Path
            directory containing `.sql` files to import, or a single `.sql` file
            (the view name is taken from the file stem)
        db_path: Path
            path to the SQLite database file
    """

    conn = sqlite3.connect(db_path)

    if path.is_dir():
        views = {}
        for file in path.iterdir():
            if not file.is_file():
                continue
            if file.suffix != ".sql":
                continue

            with open(file, "r", encoding="utf-8") as f:
                sql = f.read()
            views.setdefault(file.stem, sql)
    else:
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        views = {path.stem: sql}

    update_views(conn, views, exist_ok=True)
    conn.close()
