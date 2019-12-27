"""
Module with methods to extract database dump, and create database from dump
file, and add views to database.

This is done so that a test database can easily be recreated to have a common
starting point for testing the package.
"""

import os
import sys
import sqlite3 as sq3
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
    Create dump of database given the path to the database file

    PARAMETERS
    db_path: str: path to database file
    dump_path: str: path to the dump file to be saved
    """

    with sq3.connect(db_path) as conn:
        with open(dump_path, "w", newline="") as f:
            # noinspection PyTypeChecker
            for line in conn.iterdump():
                try:
                    f.write(line)
                except UnicodeEncodeError:
                    # for the current row, ensure all strings are ascii
                    f.write(unidecode(line))


def load_dump(db_path, dump_path):
    """
    Create test database given path to dump file

    PARAMETERS
    db_path: str: path to database file to be created
    dump_path: str: path to the dump file to be used to create database
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

    with sq3.connect(db_path) as cursor:
        try:
            cursor.executescript(sql)
        except sq3.OperationalError:
            # most likely cause is the table already exists
            pass


def add_views(db_path, view_dir):
    """
    add views to database

    PARAMETERS
    db_path: str: path to database to have views added
    view_dir: str: path the directory with view files. The contents of the
                   files are not the sql to create the view, but rather the
                   query the view should have. The view name uses the filename
                   of the query
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
