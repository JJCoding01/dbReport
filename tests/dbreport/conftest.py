import os

import pytest
import sqlite3 as sq3
from dbreport import Report
from tests.data.db_setup import load_dump, add_views
from tests.data.db_setup import TEST_PATH, DUMP_PATH, VIEW_DIR


@pytest.fixture(scope="session")
def db_connection():
    load_dump(TEST_PATH, DUMP_PATH)
    add_views(TEST_PATH, VIEW_DIR)

    cursor = sq3.connect(TEST_PATH).cursor()
    yield cursor

    cursor.close()
    try:
        os.remove(TEST_PATH)
    except PermissionError:
        print(f"could not delete {TEST_PATH}")


@pytest.fixture(scope="session")
def db_no_views():
    load_dump(TEST_PATH, DUMP_PATH)

    cursor = sq3.connect(TEST_PATH).cursor()
    yield cursor

    cursor.close()
    try:
        os.remove(TEST_PATH)
    except PermissionError:
        print(f"could not delete {TEST_PATH}")


@pytest.fixture()
def report(db_connection):
    report = Report(paths={"database": TEST_PATH})
    yield report
    print("close report fixture")


@pytest.fixture()
def rendered_reports(report):
    rendered = report.render(views=None, parse=False)
    yield rendered


def get_columns(cursor, table_name):
    """
    Return list of table column names from sqlite database
    """
    sql = """PRAGMA table_info("{}")"""
    sql = sql.format(table_name)
    c = cursor.execute(sql)
    cols = [col[1] for col in c]
    return cols
