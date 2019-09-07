from dbreport import Report
import argparse


def cli():
    """define a CLI for dbreport"""
    PARSER = argparse.ArgumentParser(
        description="generate reports from db views"
    )

    PARSER.add_argument(
        "path", nargs="?", help="path to layout file", default=None, type=str
    )

    ARGS = PARSER.parse_args()
    r = Report(ARGS.path)
    r.render_all()


if __name__ == "__main__":
    cli()
