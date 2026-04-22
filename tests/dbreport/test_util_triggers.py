import sqlite3

import pytest

from dbreport.util.triggers import (
    export_triggers,
    extract_triggers,
    import_triggers,
    update_triggers,
)

TRIGGER_SQL = "CREATE TRIGGER trg_test AFTER INSERT ON items BEGIN SELECT 1; END"
TRIGGER_SQL_V2 = "CREATE TRIGGER trg_test AFTER DELETE ON items BEGIN SELECT 1; END"
TRG_A_SQL = "CREATE TRIGGER trg_a AFTER INSERT ON items BEGIN SELECT 1; END"
TRG_B_SQL = "CREATE TRIGGER trg_b AFTER DELETE ON items BEGIN SELECT 1; END"


def make_db_with_trigger(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute(TRIGGER_SQL)
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
def conn_with_trigger(conn):
    conn.execute(TRIGGER_SQL)
    conn.commit()
    return conn


# --- extract_triggers ---


def test_extract_triggers_empty_db(conn):
    assert extract_triggers(conn) == {}


def test_extract_triggers_returns_name_and_sql(conn_with_trigger):
    result = extract_triggers(conn_with_trigger)
    assert "trg_test" in result
    assert "CREATE TRIGGER" in result["trg_test"].upper()


def test_extract_triggers_stores_full_create_sql(conn_with_trigger):
    result = extract_triggers(conn_with_trigger)
    assert result["trg_test"].upper().startswith("CREATE TRIGGER")


def test_extract_triggers_multiple(conn):
    conn.execute(TRG_A_SQL)
    conn.execute(TRG_B_SQL)
    conn.commit()
    result = extract_triggers(conn)
    assert "trg_a" in result
    assert "trg_b" in result
    assert len(result) == 2


# --- update_triggers ---


def test_update_triggers_creates_new(conn):
    update_triggers(conn, {"trg_test": TRIGGER_SQL})
    assert "trg_test" in extract_triggers(conn)


def test_update_triggers_exist_ok_true_replaces(conn_with_trigger):
    update_triggers(conn_with_trigger, {"trg_test": TRIGGER_SQL_V2}, exist_ok=True)
    result = extract_triggers(conn_with_trigger)
    assert "AFTER DELETE" in result["trg_test"].upper()


def test_update_triggers_exist_ok_false_raises(conn_with_trigger):
    with pytest.raises(sqlite3.OperationalError):
        update_triggers(conn_with_trigger, {"trg_test": TRIGGER_SQL}, exist_ok=False)


def test_update_triggers_exist_ok_false_creates_when_absent(conn):
    update_triggers(conn, {"trg_test": TRIGGER_SQL}, exist_ok=False)
    assert "trg_test" in extract_triggers(conn)


def test_update_triggers_multiple(conn):
    update_triggers(conn, {"trg_a": TRG_A_SQL, "trg_b": TRG_B_SQL})
    result = extract_triggers(conn)
    assert "trg_a" in result
    assert "trg_b" in result


# --- export_triggers ---


def test_export_triggers_creates_sql_files(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_db_with_trigger(db_path)
    export_triggers(out_dir, db_path)
    assert (out_dir / "trg_test.sql").exists()


def test_export_triggers_file_content_is_full_create_sql(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_db_with_trigger(db_path)
    export_triggers(out_dir, db_path)
    content = (out_dir / "trg_test.sql").read_text(encoding="utf-8")
    assert content.upper().startswith("CREATE TRIGGER")


def test_export_triggers_one_file_per_trigger(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute(TRG_A_SQL)
    conn.execute(TRG_B_SQL)
    conn.commit()
    conn.close()
    export_triggers(out_dir, db_path)
    sql_files = list(out_dir.glob("*.sql"))
    assert len(sql_files) == 2


def test_export_triggers_empty_db_no_files(tmp_path):
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_empty_db(db_path)
    export_triggers(out_dir, db_path)
    assert list(out_dir.iterdir()) == []


# --- import_triggers ---


def test_import_triggers_from_directory(tmp_path):
    db_path = tmp_path / "test.db"
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    make_empty_db(db_path)
    (sql_dir / "trg_test.sql").write_text(TRIGGER_SQL, encoding="utf-8")
    import_triggers(sql_dir, db_path)
    conn = sqlite3.connect(db_path)
    result = extract_triggers(conn)
    conn.close()
    assert "trg_test" in result


def test_import_triggers_ignores_non_sql_files(tmp_path):
    db_path = tmp_path / "test.db"
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    make_empty_db(db_path)
    (sql_dir / "trg_test.sql").write_text(TRIGGER_SQL, encoding="utf-8")
    (sql_dir / "notes.txt").write_text("not sql", encoding="utf-8")
    import_triggers(sql_dir, db_path)
    conn = sqlite3.connect(db_path)
    result = extract_triggers(conn)
    conn.close()
    assert "notes" not in result
    assert "trg_test" in result


def test_import_triggers_from_single_file(tmp_path):
    db_path = tmp_path / "test.db"
    sql_file = tmp_path / "trg_test.sql"
    make_empty_db(db_path)
    sql_file.write_text(TRIGGER_SQL, encoding="utf-8")
    import_triggers(sql_file, db_path)
    conn = sqlite3.connect(db_path)
    result = extract_triggers(conn)
    conn.close()
    assert "trg_test" in result


def test_import_triggers_round_trip(tmp_path):
    db1 = tmp_path / "db1.db"
    db2 = tmp_path / "db2.db"
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    make_db_with_trigger(db1)
    make_empty_db(db2)
    export_triggers(export_dir, db1)
    import_triggers(export_dir, db2)
    conn1 = sqlite3.connect(db1)
    conn2 = sqlite3.connect(db2)
    result1 = extract_triggers(conn1)
    result2 = extract_triggers(conn2)
    conn1.close()
    conn2.close()
    assert result1.keys() == result2.keys()
    assert result1["trg_test"] == result2["trg_test"]
