import os

import pytest
from bs4 import BeautifulSoup
from conftest import get_columns

from dbreport.dbreport import Report
from tests.data.db_setup import VIEW_DIR


def test_init():

    with pytest.raises(FileNotFoundError):
        Report("layout_that_does_not_exist.json")

    with pytest.raises(ValueError):
        # only the path to the layout file is given as a positional argument.
        # The remaining parameters are parameters from the layout file given as
        # keyword arguments. If any keyword arguments are given, the path to
        # the layout file must be None
        Report("layout_path.json", path="any_keyword_argument_db.db")


def test_database_connection(db_connection):

    with pytest.raises(FileNotFoundError):
        Report(paths={"database": "database_that_does_not_exist.db"})


def test_report_names(rendered_reports):
    """Validate a report is generated for all views"""

    view_names = list(rendered_reports.keys())
    for file in os.listdir(VIEW_DIR):
        # strip .sql extension from filename to get the view name
        view_name = file[:-4]
        assert view_name in view_names


def test_subset_report_names(report):

    reports = report.render(views=None, parse=False)
    view_names = list(reports.keys())

    # render only specific reports
    check_views = [view_names[0], view_names[3]]
    reports = report.render(views=check_views, parse=False)
    for view, key in zip(check_views, reports.keys()):
        assert view == key

    # render a single view given the name as a string
    reports = report.render(views=check_views[0], parse=False)
    assert check_views[0] == list(reports.keys())[0]


def test_content_title(rendered_reports):

    for r in rendered_reports:
        soup = BeautifulSoup(rendered_reports[r], features="html.parser")
        assert soup.title.text == r


def test_content_filters(rendered_reports, db_connection):

    for r in rendered_reports:
        soup = BeautifulSoup(rendered_reports[r], features="html.parser")
        columns = get_columns(db_connection, r)
        tags = soup.find_all("input")
        assert len(tags) == len(columns)
        for tag in tags:
            assert tag["id"] in columns


def test_write(report, rendered_reports):
    paths = [".", None]
    for path in paths:
        report.write(path)
        for view, html in rendered_reports.items():
            with open(f"{view}.html", "r") as f:
                assert html == f.read()
            os.remove(f"{view}.html")


def test_write_invalid_report_path(report):

    with pytest.raises(NotADirectoryError):
        report.write("not_a_directory")
