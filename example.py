import os
from dbreport import Report
from tests.data.db_setup import DUMP_PATH, VIEW_DIR, load_dump, add_views

# filename for example database. Replace with path to your own database.
DB_FILENAME = "example.db"

# Directory for sample reports. Replace with path where you want your own
# reports saved
REPORTS_DIR = "reports"


class MyCustomReport(Report):
    """
    Custom class that inherits from Report and implements the parse method
    """

    # def __init__(self, **kwargs):
    #     super(MyCustomReport, self).__init__(*kwargs)

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

    # 0. I assume you have your own database you want to create a report for.
    # So you will not need to set up the database when using your own.
    # This function simply creates a database to run the examples.
    db_setup()

    # 1. Start of code for generating report.
    # Generate a report object by giving it the database path
    report = Report(paths={"database": DB_FILENAME})

    # 2. Write the reports
    report.write(REPORTS_DIR)

    # 2.1 or you can access the rendered html as text using
    # rendered_reports = report.render()

    # 3. Open first report in default application for html (hopefully it's
    # a browser. If not, you probably know how to open it in one.)
    os.system(os.path.join(REPORTS_DIR, "listEmployees.html"))


def example_parse():
    """
    Example showing how to use the parse function
    """

    # 0. I assume you have your own database you want to create a report for.
    # So you will not need to set up the database when using your own.
    # This function simply creates a database to run the examples.
    db_setup()

    # 1. Start of code for generating report.
    # Generate a report object by giving it the database path
    report = MyCustomReport(paths={"database": DB_FILENAME})

    # 2. Write the reports. Be sure the parse parameter is set to True
    report.write(REPORTS_DIR, parse=True)

    # 2.1 or you can access the rendered html as text using
    # rendered_reports = report.render(parse=True)

    # 3. Open first report in default application for html (hopefully it's
    # a browser. If not, you probably know how to open it in one.)
    os.system(os.path.join(REPORTS_DIR, "listEmployees.html"))


def example_categories():
    """
    Example with categories and custom titles
    """

    # 0. I assume you have your own database you want to create a report for.
    # So you will not need to set up the database when using your own.
    # This function simply creates a database to run the examples.
    db_setup()

    # 1. Start of code for generating report.
    # Generate a report object by giving it the database path.
    # The categories are Employees and Customers, and Misc (included
    # automatically). The contents of the Employees category are links to the
    # reports for views listEmployees and topSalesmen. The Misc category is a
    # catch all that includes links to all reports not listed in other
    # categories.
    report = Report(
        paths={"database": DB_FILENAME},
        categories={
            "Employees": ["listEmployees", "topSalesmen"],
            "Customers": ["topCustomer"],
        },
        titles={"listEmployees": "list of Employees"},
    )

    # 2. Write the reports. Be sure the parse parameter is set to True
    report.write(REPORTS_DIR)

    # 2.1 or you can access the rendered html as text using
    # rendered_reports = report.render()

    # 3. Open first report in default application for html (hopefully it's
    # a browser. If not, you probably know how to open it in one.)
    os.system(os.path.join(REPORTS_DIR, "listEmployees.html"))


if __name__ == "__main__":
    # example_simple()
    # example_parse()
    example_categories()
