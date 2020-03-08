import os
import sqlite3 as sq3

import pytest

from dbreport import Report
from tests.data.db_setup import (DUMP_PATH, TEST_PATH, VIEW_DIR,
                                 add_views, load_dump)


@pytest.fixture(scope="session")
def db_connection():
    load_dump(TEST_PATH, DUMP_PATH)
    add_views(TEST_PATH, VIEW_DIR)

    conn = sq3.connect(TEST_PATH)
    cursor = conn.cursor()
    yield cursor

    cursor.close()
    conn.close()
    try:
        os.remove(TEST_PATH)
    except PermissionError:
        print(f"could not delete {TEST_PATH}")


@pytest.fixture(scope="session")
def db_no_views():
    load_dump(TEST_PATH, DUMP_PATH)

    conn = sq3.connect(TEST_PATH)
    cursor = conn.cursor()
    yield cursor

    conn = sq3.connect(TEST_PATH)
    cursor = conn.cursor()
    yield cursor

    cursor.close()
    conn.close()
    try:
        os.remove(TEST_PATH)
    except PermissionError:
        print(f"could not delete {TEST_PATH}")


@pytest.fixture()
def report(db_connection):
    report = Report(paths={"database": TEST_PATH, "report_dir": "."})
    yield report


@pytest.fixture()
def report_with_categories_with_misc(db_connection, views):
    categories = {"cat1": views[0:3]}
    report = Report(paths={"database": TEST_PATH, "report_dir": "."},
                    categories=categories)
    yield report


@pytest.fixture()
def report_with_categories_without_misc(db_connection, views):
    report = Report(paths={"database": TEST_PATH, "report_dir": "."},
                    categories={"cat1": views})
    yield report


@pytest.fixture()
def rendered_reports(report):
    rendered = report.render(views=None, parse=False)
    yield rendered


@pytest.fixture(scope="session")
def views():
    view_names = []
    for file in os.listdir(VIEW_DIR):
        view_names.append(file[:-4])  # strip .sql from filename
    return view_names


@pytest.fixture(scope="session")
def get_columns(*args, **kwargs):
    def columns(cursor, table_name):
        """
        Return list of table column names from sqlite database
        """
        sql = """PRAGMA table_info("{}")"""
        sql = sql.format(table_name)
        c = cursor.execute(sql)
        cols = [col[1] for col in c]
        return cols

    return columns
