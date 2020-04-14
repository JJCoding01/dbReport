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


def test_init_with_non_existent_layout():
    with pytest.raises(FileNotFoundError):
        Report("layout_that_does_not_exist.json")


def test_init_with_both_layout_path_and_kwargs():
    with pytest.raises(ValueError):
        # only the path to the layout file is given as a positional argument.
        # The remaining parameters are parameters from the layout file given as
        # keyword arguments. If any keyword arguments are given, the path to
        # the layout file must be None
        Report("layout_path.json", path="any_keyword_argument_db.db")


def test_property_categories(report, views):
    # when no categories are given, it should have one category (Misc) that
    # contains all views
    categories = report.categories
    assert len(categories) == 1, "Default category length should have one item"
    assert list(categories.keys())[0] == "Misc", "default category not 'Misc'"
    assert (
            categories.get("Misc", []).sort() == views.sort()
    ), "default category does not have all views"


def test_property_categories_invalid(report):
    with pytest.raises(TypeError):
        report.categories = ""  # not a dictionary


def test_property_categories_invalid_key_not_str(report):
    with pytest.raises(TypeError):
        report.categories = {1: ["a list"]}  # category is not a str


def test_property_categories_invalid_key_not_list(report):
    with pytest.raises(TypeError):
        report.categories = {"my category": "not a list"}


def test_property_categories_invalid_not_dict(report):
    with pytest.raises(TypeError):
        report.categories = "not a dict"


def test_property_categories_invalid_value_with_invalid_view(report):
    with pytest.raises(ValueError):
        report.categories = {"my category": ["view name that does not exist"]}


def test_property_category_has_misc(report):
    assert "Misc" in report.categories.keys(), "default Misc not included"


def test_property_category_add_items(report, views):
    report.categories = {"category 1": views[0:1], "category 2": views[3:4]}
    assert "category 1" in report.categories.keys()
    assert "category 2" in report.categories.keys()
    assert "Misc" not in report.categories.keys()


def test_property_category_without_misc(report, views):
    report.categories = {"Some Category": views}
    assert "Misc" not in report.categories.keys(), "default Misc not included"


def test_categories_with_misc(report_with_categories_with_misc):
    report = report_with_categories_with_misc
    assert "Misc" in report.categories.keys()


def test_categories_without_misc(report_with_categories_without_misc):
    report = report_with_categories_without_misc
    assert "Misc" not in report.categories.keys()


def test_property_views(report, views):
    assert (
            report.views.sort() == views.sort()
    ), "report views does not match expected"


def test_property_views_read_only(report):
    with pytest.raises(AttributeError):
        report.views = "any value"  # views property is read-only


def test_add_ignore_views(report):
    report.ignore = ["popularArtists", "topSalesmen"]
    assert report.ignore == ["popularArtists", "topSalesmen"]


def test_add_invalid_ignore_views(report):
    with pytest.raises(ValueError):
        report.ignore = ["popularArtists", "view_name_that_does_not_exist"]


def test_ignored_views_are_removed(report):
    report.ignore = ["listEmployees", "popularArtists"]
    for view in report.ignore:
        assert view not in report.views, "ignored view is still included"


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


def test_rendered_report_has_patched_date(rendered_reports, datetime_constant):
    date_str = datetime_constant.strftime("%Y-%m-%dT%H:%M:%S")
    for html in rendered_reports.values():
        assert date_str in html


def test_write(report, rendered_reports, datetime_constant):
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


def test_layout_ignore_views(report_from_layout):
    report, layout = report_from_layout
    reports = report.render()
    ignore_view = 'popularArtists'
    assert (
            ignore_view not in reports.keys()
    ), f"ignored view '{ignore_view}' was still rendered"
