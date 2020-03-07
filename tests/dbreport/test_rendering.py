"""
Test module to validate the actual rendering
"""

from bs4 import BeautifulSoup

from dbreport.dbreport import Report
from tests.data.db_setup import TEST_PATH


def test_captions(db_connection, views):
    report = Report(
        paths={"database": TEST_PATH},
        captions={view: f"caption for view {view}" for view in views},
    )
    rendered = report.render()
    for view, html in rendered.items():
        soup = BeautifulSoup(html, features="html.parser")
        caption = soup.find("caption")
        assert (
                caption.text == f"caption for view {view}"
        ), "caption does match expected value"


def test_categories_with_misc():
    # create several categories, but leave at lease one (1) view not in any
    # category.
    categories = {
        "Employees": ["listEmployees", "topSalesmen"],
        "Customers": ["topCustomer"],
    }
    report = Report(
        paths={"database": TEST_PATH, "report_dir": "."}, categories=categories
    )
    rendered = report.render()

    for v, html in rendered.items():
        soup = BeautifulSoup(html, features="html.parser")
        buttons = soup.find_all(
            "button", class_="dropbtn theme-d5 hover-theme"
        )

        # compare the length of rendered categories and input categories. The
        # rendered categories should be one more than the input categories
        # since it will have the automatically added Misc category
        assert (
                len(categories) == len(buttons) - 1
        ), "number of rendered categories does not match input categories"

        for category, button in zip(categories, buttons):
            assert (
                    category == button.text
            ), "input category does not match rendered category"


def test_content_filters(rendered_reports, db_connection, get_columns):
    for r in rendered_reports:
        soup = BeautifulSoup(rendered_reports[r], features="html.parser")
        columns = get_columns(db_connection, r)
        tags = soup.find_all("input")
        assert len(tags) == len(
            columns
        ), "different number of filters and columns"
        for tag in tags:
            assert (
                    tag["id"] in columns
            ), f"missing id value '{tag['id']}' in filter inputs"


def test_content_title(rendered_reports):
    for r in rendered_reports:
        soup = BeautifulSoup(rendered_reports[r], features="html.parser")
        assert soup.title.text == r, "title text not found in rendered report"


def test_descriptions(db_connection, views):
    description = "description for view {}"
    report = Report(
        paths={"database": TEST_PATH},
        descriptions={view: description.format(view) for view in views},
    )
    rendered = report.render()
    for view, html in rendered.items():
        soup = BeautifulSoup(html, features="html.parser")
        description_tag = soup.find("p", class_="description")
        assert description_tag.text == description.format(
            view
        ), "descriptions do not match"


def test_titles(db_connection, views):
    report = Report(
        paths={"database": TEST_PATH},
        titles={view: view.upper() for view in views},
    )
    rendered = report.render()
    for view, html in rendered.items():
        soup = BeautifulSoup(html, features="html.parser")
        title = soup.find("title")
        assert title.text == view.upper(), "title does match expected value"
