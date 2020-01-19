"""
Define the CLI for the dbreport module.
"""
import argparse

from dbreport.dbreport import Report


def cli():
    """define a CLI for dbreport"""
    parser = argparse.ArgumentParser(
        description="generate reports from db views"
    )

    parser.add_argument(
        "path", nargs="?", help="path to layout file", default=None, type=str
    )

    args = parser.parse_args()
    report = Report(args.path)
    report.render(parse=False)


if __name__ == "__main__":
    cli()
