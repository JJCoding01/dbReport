import json
import os
import shutil
import sqlite3 as sq3

from datetime import datetime
from pathlib import Path

import pytest

from dbreport import Report
from tests.data.db_setup import add_views, DUMP_PATH, load_dump, TEST_PATH, VIEW_DIR


@pytest.fixture()
def datetime_constant():
    yield datetime(2020, 1, 1, 0, 0, 0)  # 2020-01-01 00:00:00


@pytest.fixture()
def patch_datetime(monkeypatch, datetime_constant):
    class mydatetime:
        @classmethod
        def now(cls):
            return datetime_constant

    monkeypatch.setattr("dbreport.report.datetime", mydatetime)


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


@pytest.fixture()
def report(db_connection, tmp_path):
    import dbreport as _dbreport

    src_css = Path(_dbreport.__file__).parent / "templates" / "static" / "css"
    static_dir = tmp_path / "static"
    shutil.copytree(src_css, static_dir / "css")
    report = Report(
        paths={
            "database": TEST_PATH,
            "report_dir": ".",
            "static": str(static_dir),
        }
    )
    yield report
    report.close()


@pytest.fixture()
def report_with_categories_with_misc(db_connection, views):
    categories = {"cat1": views[0:3]}
    report = Report(
        paths={"database": TEST_PATH, "report_dir": "."}, categories=categories
    )
    yield report
    report.close()


@pytest.fixture()
def report_with_categories_without_misc(db_connection, views):
    report = Report(
        paths={"database": TEST_PATH, "report_dir": "."},
        categories={"cat1": views},
    )
    yield report
    report.close()


@pytest.fixture()
def rendered_reports(report, patch_datetime):
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


@pytest.fixture(scope="session")
def report_from_layout(db_connection):
    """
    Create a layout file, yield ``(report, layout)``, and delete the file on teardown.
    """
    path = os.path.abspath(os.path.join(".", "layout.json"))
    layout = {
        "paths": {"database": TEST_PATH, "report_dir": "."},
        "ignore_views": ["popularArtists"],
    }
    with open(path, "w") as f:
        f.write(json.dumps(layout))
    report = Report(path)
    yield report, layout
    report.close()
    os.remove(path)
