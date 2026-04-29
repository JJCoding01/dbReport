import os

from dbreport import Report
from tests.data.db_setup import TEST_PATH


def test_kwargs_override_layout_file(report_from_layout):
    """kwargs values take precedence over the user layout file."""
    _, _ = report_from_layout
    path = os.path.abspath(os.path.join(".", "layout.json"))
    # layout file has ignore_views=["popularArtists"]; kwarg should win
    report = Report(path, ignore_views=[])
    assert report.ignore_views == []
    report.close()


def test_layout_file_overrides_defaults(report_from_layout):
    """User layout file values take precedence over package defaults."""
    report, _ = report_from_layout
    # layout file specifies ignore_views=["popularArtists"]
    assert "popularArtists" in report.ignore_views


def test_kwargs_only_uses_package_defaults(db_connection):
    """When no layout file is given, missing keys come from the package defaults."""
    report = Report(paths={"database": TEST_PATH, "report_dir": "."})
    assert report.paths.static != ""
    report.close()


def test_kwargs_paths_resolve_relative_to_cwd(db_connection):
    """Paths in kwargs are resolved relative to the caller's cwd."""
    rel_db = os.path.relpath(TEST_PATH, os.getcwd())
    report = Report(paths={"database": rel_db, "report_dir": "."})
    assert os.path.exists(report.paths.database)
    report.close()


def test_three_layers_all_present(report_from_layout, db_connection):
    """
    All three layers combined

    Defaults fill gaps, file overrides defaults, kwargs override file.
    """
    _, _ = report_from_layout
    path = os.path.abspath(os.path.join(".", "layout.json"))
    # layout file: ignore_views=["popularArtists"], no titles
    # kwargs: ignore_views=[], titles={"listAlbums": "Albums"}
    report = Report(path, ignore_views=[], titles={"listAlbums": "Albums"})
    assert report.ignore_views == []  # kwargs win over file
    assert report.titles == {"listAlbums": "Albums"}  # kwargs fill missing key
    assert report.paths.static != ""  # defaults fill gap
    report.close()
