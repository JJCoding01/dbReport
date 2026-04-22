import sqlite3

import pytest

from dbreport.util.views import (
    CREATE_VIEW_RE,
    export_views,
    extract_views,
    import_views,
    update_views,
)

VIEW_SELECT_SQL = "SELECT id, name FROM items"
VIEW_SELECT_SQL_V2 = "SELECT id FROM items"


def make_db_with_view(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute(f'CREATE VIEW "vw_test" AS {VIEW_SELECT_SQL}')
    conn.commit()
    conn.close()


def make_empty_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.commit()
    conn.close()


@pytest.fixture()
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    connection.commit()
    yield connection
    connection.close()


@pytest.fixture()
def conn_with_view(conn):
    conn.execute(f'CREATE VIEW "vw_test" AS {VIEW_SELECT_SQL}')
    conn.commit()
    return conn


# --- CREATE_VIEW_RE ---


@pytest.mark.parametrize(
    "full_sql,expected",
    [
        ("CREATE VIEW vw_test AS SELECT 1", "SELECT 1"),
        ('CREATE VIEW "vw_test" AS SELECT 1', "SELECT 1"),
        ("CREATE VIEW `vw_test` AS SELECT 1", "SELECT 1"),
        ("CREATE VIEW [vw_test] AS SELECT 1", "SELECT 1"),
        ("create view vw_test as SELECT 1", "SELECT 1"),
        ("  CREATE  VIEW  vw_test  AS  SELECT 1", "SELECT 1"),
    ],
)
def test_create_view_re_strips_prefix(full_sql, expected):
    assert CREATE_VIEW_RE.sub("", full_sql, count=1) == expected


def test_create_view_re_no_match_on_plain_select():
    sql = "SELECT id FROM items"
    assert CREATE_VIEW_RE.sub("", sql, count=1) == sql


# --- extract_views ---


def test_extract_views_empty_db(conn):
    assert extract_views(conn) == {}


def test_extract_views_returns_select_only(conn_with_view):
    result = extract_views(conn_with_view)
    assert "vw_test" in result
    assert not result["vw_test"].upper().startswith("CREATE")
    assert result["vw_test"].upper().startswith("SELECT")


def test_extract_views_multiple(conn):
    conn.execute(f'CREATE VIEW "vw_a" AS {VIEW_SELECT_SQL}')
    conn.execute(f'CREATE VIEW "vw_b" AS {VIEW_SELECT_SQL_V2}')
    conn.commit()
    result = extract_views(conn)
    assert "vw_a" in result
    assert "vw_b" in result
    assert len(result) == 2


# --- update_views ---


def test_update_views_creates_new(conn):
    update_views(conn, {"vw_test": VIEW_SELECT_SQL})
    assert "vw_test" in extract_views(conn)


def test_update_views_exist_ok_true_replaces(conn_with_view):
    update_views(conn_with_view, {"vw_test": VIEW_SELECT_SQL_V2}, exist_ok=True)
    result = extract_views(conn_with_view)
    assert result["vw_test"] == VIEW_SELECT_SQL_V2


def test_update_views_exist_ok_false_raises(conn_with_view):
    with pytest.raises(sqlite3.OperationalError):
        update_views(conn_with_view, {"vw_test": VIEW_SELECT_SQL}, exist_ok=False)


def test_update_views_exist_ok_false_creates_when_absent(conn):
    update_views(conn, {"vw_test": VIEW_SELECT_SQL}, exist_ok=False)
    assert "vw_test" in extract_views(conn)


def test_update_views_select_sql_round_trip(conn):
    update_views(conn, {"vw_test": VIEW_SELECT_SQL})
    result = extract_views(conn)
    assert result["vw_test"] == VIEW_SELECT_SQL


def test_update_views_multiple(conn):
    update_views(conn, {"vw_a": VIEW_SELECT_SQL, "vw_b": VIEW_SELECT_SQL_V2})
    result = extract_views(conn)
    assert "vw_a" in result
    assert "vw_b" in result


# --- export_views ---


def test_export_views_creates_sql_files(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_db_with_view(db_path)
    export_views(out_dir, db_path)
    assert (out_dir / "vw_test.sql").exists()


def test_export_views_file_content_is_select_only(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_db_with_view(db_path)
    export_views(out_dir, db_path)
    content = (out_dir / "vw_test.sql").read_text(encoding="utf-8")
    assert not content.upper().startswith("CREATE")
    assert content == VIEW_SELECT_SQL


def test_export_views_one_file_per_view(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute(f'CREATE VIEW "vw_a" AS {VIEW_SELECT_SQL}')
    conn.execute(f'CREATE VIEW "vw_b" AS {VIEW_SELECT_SQL_V2}')
    conn.commit()
    conn.close()
    export_views(out_dir, db_path)
    sql_files = list(out_dir.glob("*.sql"))
    assert len(sql_files) == 2


def test_export_views_empty_db_no_files(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_empty_db(db_path)
    export_views(out_dir, db_path)
    assert list(out_dir.iterdir()) == []


# --- import_views ---


def test_import_views_from_directory(tmp_path):
    db_path = tmp_path / "test.db"
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    make_empty_db(db_path)
    (sql_dir / "vw_test.sql").write_text(VIEW_SELECT_SQL, encoding="utf-8")
    import_views(sql_dir, db_path)
    conn = sqlite3.connect(db_path)
    result = extract_views(conn)
    conn.close()
    assert "vw_test" in result


def test_import_views_ignores_non_sql_files(tmp_path):
    db_path = tmp_path / "test.db"
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    make_empty_db(db_path)
    (sql_dir / "vw_test.sql").write_text(VIEW_SELECT_SQL, encoding="utf-8")
    (sql_dir / "notes.txt").write_text("not sql", encoding="utf-8")
    import_views(sql_dir, db_path)
    conn = sqlite3.connect(db_path)
    result = extract_views(conn)
    conn.close()
    assert "notes" not in result
    assert "vw_test" in result


def test_import_views_from_single_file(tmp_path):
    db_path = tmp_path / "test.db"
    sql_file = tmp_path / "vw_test.sql"
    make_empty_db(db_path)
    sql_file.write_text(VIEW_SELECT_SQL, encoding="utf-8")
    import_views(sql_file, db_path)
    conn = sqlite3.connect(db_path)
    result = extract_views(conn)
    conn.close()
    assert "vw_test" in result


def test_import_views_round_trip(tmp_path):
    db1 = tmp_path / "db1.db"
    db2 = tmp_path / "db2.db"
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    make_db_with_view(db1)
    make_empty_db(db2)
    export_views(export_dir, db1)
    import_views(export_dir, db2)
    conn2 = sqlite3.connect(db2)
    result = extract_views(conn2)
    conn2.close()
    assert result["vw_test"] == VIEW_SELECT_SQL
