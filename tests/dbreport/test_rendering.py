"""
Test module to validate the actual rendering
"""

from bs4 import BeautifulSoup

from dbreport import Report
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
            caption.get_text(strip=True) == f"caption for view {view}"
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
        buttons = soup.find_all("button", class_="dropbtn theme-d5 hover-theme")

        # compare the length of rendered categories and input categories. The
        # rendered categories should be one more than the input categories
        # since it will have the automatically added Misc category
        assert (
            len(categories) == len(buttons) - 1
        ), "number of rendered categories does not match input categories"

        for category, button in zip(categories, buttons):
            assert category == button.get_text(
                strip=True
            ), "input category does not match rendered category"


def test_content_filters(rendered_reports, db_connection, get_columns):
    """Filter inputs are injected by DataTables at runtime into a second thead row."""
    for r in rendered_reports:
        soup = BeautifulSoup(rendered_reports[r], features="html.parser")
        columns = get_columns(db_connection, r)

        assert (
            soup.find("form", class_="filter-form") is None
        ), "old filter-form should not be present"

        thead = soup.find("thead")
        assert thead is not None, "thead must be present"
        header_rows = thead.find_all("tr")
        assert (
            len(header_rows) == 2
        ), "thead must have two rows: labels and filter inputs"
        filter_cells = header_rows[1].find_all("th")
        assert len(filter_cells) == len(
            columns
        ), "second thead row must have one <th> per column"


def test_content_title(rendered_reports):
    for r in rendered_reports:
        soup = BeautifulSoup(rendered_reports[r], features="html.parser")
        assert (
            soup.title.get_text(strip=True) == r
        ), "title text not found in rendered report"


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
        assert description_tag.get_text(strip=True) == description.format(
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
        assert (
            title.get_text(strip=True) == view.upper()
        ), "title does match expected value"


def test_render_matches_write(report, patch_datetime, tmp_path):
    """render() and write() produce identical HTML."""
    rendered = report.render()
    written = report.write(str(tmp_path))
    for view in rendered:
        assert rendered[view] == written[view]


def test_write_html_references_static_assets(report, tmp_path):
    """Written HTML files reference assets under the static/ subdirectory."""
    report.write(str(tmp_path))
    html_files = list(tmp_path.glob("*.html"))
    assert html_files, "no HTML files written"
    soup = BeautifulSoup(html_files[0].read_text(), "html.parser")
    hrefs = [tag["href"] for tag in soup.find_all("link", href=True)]
    srcs = [
        tag["src"]
        for tag in soup.find_all("script", src=True)
        if tag.get("src", "").startswith("static")
    ]
    assert any("static" in h for h in hrefs), "no static css href in HTML"
    assert srcs, "no static js src in HTML"
