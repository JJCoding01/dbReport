"""
Module with methods to extract database dump, and create database from dump
file, and add views to database.

This is done so that a test database can easily be recreated to have a common
starting point for testing the package.
"""

import os
import sqlite3 as sq3
import sys

from text_unidecode import unidecode

# set up paths for where to find original database
BASE_PATH = os.path.split(os.path.abspath(__file__))[0]
BASE_DATABASE_FILENAME = "chinook.db"
BASE_DATABASE_PATH = os.path.join(BASE_PATH, BASE_DATABASE_FILENAME)

# Or where to find dump file and create test database
DUMP_PATH = os.path.join(BASE_PATH, f"{BASE_DATABASE_FILENAME[:-3]}_dump.sql")
TEST_PATH = os.path.join(BASE_PATH, f"test_{BASE_DATABASE_FILENAME}")
VIEW_DIR = os.path.join(BASE_PATH, "views")


def extract_dump(db_path, dump_path):
    """
    Create a dump of the database.

    Parameters
    ----------
    db_path : str
        Path to the database file.
    dump_path : str
        Path where the dump file will be saved.
    """

    conn = sq3.connect(db_path)
    try:
        with open(dump_path, "w", newline="") as f:
            # noinspection PyTypeChecker
            for line in conn.iterdump():
                f.write(unidecode(line))
    finally:
        conn.close()


def load_dump(db_path, dump_path):
    """
    Create a test database from a dump file.

    Parameters
    ----------
    db_path : str
        Path to the database file to be created.
    dump_path : str
        Path to the dump file used to create the database.
    """

    # start by removing the existing database if one exists
    try:
        os.remove(db_path)
    except PermissionError:
        print(f"could not delete {db_path}, continuing anyway")
    except FileNotFoundError:
        # if the file was not found, nothing needs to be done.
        pass

    with open(dump_path, "r") as f:
        sql = f.read()

    conn = sq3.connect(db_path)
    try:
        try:
            conn.executescript(sql)
        except sq3.OperationalError:
            # most likely cause is the table already exists
            pass
        conn.commit()
    finally:
        conn.close()


def add_views(db_path, view_dir):
    """
    Add views to the database from SQL files.

    Parameters
    ----------
    db_path : str
        Path to the database to have views added.
    view_dir : str
        Path to the directory containing view files. Each file holds the
        SELECT query for the view; the view name is taken from the filename.
    """

    conn = sq3.connect(db_path)
    cursor = conn.cursor()

    for file in os.listdir(view_dir):
        if not file.lower().endswith(".sql"):
            # skip all non .sql files
            continue
        path = os.path.join(view_dir, file)
        sql = f"CREATE VIEW IF NOT EXISTS [{file[:-4]}] AS\n"
        with open(path, "r") as f:
            sql += f.read()
        try:
            cursor.execute(sql)
            conn.commit()
        except sq3.OperationalError:
            print(f"failed to create view {file}")
            continue

    cursor.close()
    conn.close()


if __name__ == "__main__":
    args = sys.argv[1]
    if args == "create-dump":
        # to extract database and create dump file run...
        extract_dump(BASE_DATABASE_PATH, DUMP_PATH)
    elif args == "load-dump":
        # to load dump file and create test db run...
        load_dump(TEST_PATH, DUMP_PATH)
        add_views(TEST_PATH, VIEW_DIR)
    else:
        print("did not create anything")
