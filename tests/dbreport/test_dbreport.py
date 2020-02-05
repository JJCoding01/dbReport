import os

import pytest

from dbreport.dbreport import Report


def test_all_views_are_rendered(rendered_reports, views):
    """Validate a report is generated for all views"""

    rendered_view_names = list(rendered_reports.keys())
    for view_name in views:
        assert (
                view_name in rendered_view_names
        ), f"missing view '{view_name}' in rendered views"


def test_database_connection(db_connection):
    with pytest.raises(FileNotFoundError):
        Report(paths={"database": "database_that_does_not_exist.db"})


def test_init():

    with pytest.raises(FileNotFoundError):
        Report("layout_that_does_not_exist.json")

    with pytest.raises(ValueError):
        # only the path to the layout file is given as a positional argument.
        # The remaining parameters are parameters from the layout file given as
        # keyword arguments. If any keyword arguments are given, the path to
        # the layout file must be None
        Report("layout_path.json", path="any_keyword_argument_db.db")


def test_render_single_view_name_as_string(report, views):
    # render a single view given the name as a string
    reports = report.render(views=views[0], parse=False)
    assert (
            views[0] == list(reports.keys())[0]
    ), "rendered report does not match requested"


def test_subset_views_are_rendered(report, views):
    # render only specific reports
    check_views = [views[0], views[-1]]
    reports = report.render(views=check_views, parse=False)
    for view, key in zip(check_views, reports.keys()):
        assert view == key, "rendered report name does not match requested"


def test_write(report, rendered_reports):
    paths = [".", None]
    for path in paths:
        report.write(path)
        for view, html in rendered_reports.items():
            with open(f"{view}.html", "r") as f:
                assert html == f.read(), f"failed for path: {path}"
            os.remove(f"{view}.html")


def test_write_invalid_report_path(report):

    with pytest.raises(NotADirectoryError):
        report.write("not_a_directory")
