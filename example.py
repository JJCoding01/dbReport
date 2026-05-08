import os

from dbreport import Report
from tests.data.db_setup import add_views, DUMP_PATH, load_dump, VIEW_DIR

# filename for example database. Replace with path to your own database.
DB_FILENAME = "example.db"

# Directory for sample reports. Replace with path where you want your own
# reports saved
REPORTS_DIR = "reports"


class MyCustomReport(Report):
    """
    Custom class that inherits from Report and implements the parse method
    """

    def parse(self, data):
        """
        define how the data should be parsed before getting rendered

        For this example, we will make all text upper case.
        """
        updated_data = {}
        for view, rows in data.items():
            updated_rows = []
            for row in rows:
                updated_rows.append(
                    [c.upper() if isinstance(c, str) else c for c in row]
                )
            updated_data.setdefault(view, updated_rows)

        # note returned data is in the same format as input parameter data.
        return updated_data


def db_setup():
    # 0.1. Add reports directory, if it does not already exist
    try:
        os.mkdir(REPORTS_DIR)
    except FileExistsError:
        pass

    # 0.2. create the example database, loaded with data, and create the views
    # used for testing
    load_dump(DB_FILENAME, DUMP_PATH)
    add_views(DB_FILENAME, VIEW_DIR)


def example_simple():
    """
    Simple example using default Report generator

    Use default report generator, no parsing, and no additional parameters.
    """
    # 1. Start of code for generating report.
    # Generate a report object by giving it the database and output paths.
    report = Report(paths={"report_dir": REPORTS_DIR, "database": DB_FILENAME})

    # 2. Write the reports
    report.generate()  # first run, copies static folder

    # After `report.generate()` runs, it is sufficient to use `report.write()`
    # to update the reports any time the database changes. This will skip the
    # setup of the static dir.
    # report.write()

    # 2.1 or you can access the rendered html as text using
    # rendered_reports = report.render()


def example_parse():
    """
    Example showing how to use the parse function
    """

    # 1. Start of code for generating report.
    # Generate a report object by giving it the database and output paths.
    report = MyCustomReport(paths={"database": DB_FILENAME, "report_dir": REPORTS_DIR})

    # 2. Write the reports. Be sure the parse parameter is set to True
    report.generate(parse=True)  # generate the first time

    # After `report.generate()` runs, it is sufficient to use `report.write()`
    # to update the reports any time the database changes. This will skip the
    # setup of the static dir.
    # report.write(parse=True)


def example_categories():
    """
    Example with categories and custom titles
    """
    # 1. Start of code for generating report.
    # Generate a report object by giving it the database and output paths.
    # The categories are `Employees` and `Customers`, and `Misc` (included
    # automatically). The contents of the Employees category are links to the
    # reports for views `listEmployees` and `topSalesmen`. The `Misc` category
    # is a catch all that includes links to all reports not listed in other
    # categories.
    report = Report(
        paths={
            "database": DB_FILENAME,
            "report_dir": REPORTS_DIR,
        },
        categories={
            "Employees": ["listEmployees", "topSalesmen"],
            "Customers": ["topCustomer"],
        },
        titles={"listEmployees": "list of Employees"},
        descriptions={
            "topCustomer": "Some text to describe or introduce the "
            "table. May be as extensive as you need it to be."
        },
    )

    # 2. Write the reports. Be sure the parse parameter is set to True
    report.generate(parse=False)

    # After `report.generate()` runs, it is sufficient to use `report.write()`
    # to update the reports any time the database changes. This will skip the
    # setup of the static dir.
    # report.write(parse=True)


if __name__ == "__main__":
    # set up the database
    db_setup()

    # run various report examples here
    # example_simple()
    # example_parse()
    example_categories()
