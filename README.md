Readme
=======

[![Build Status](https://travis-ci.org/josephjcontreras/dbReport.svg?branch=master)](https://travis-ci.org/josephjcontreras/dbReport)
[![Coverage Status](https://coveralls.io/repos/github/josephjcontreras/dbReport/badge.svg?branch=master)](https://coveralls.io/github/josephjcontreras/dbReport?branch=master)
[![Documentation Status](https://readthedocs.org/projects/dbreport/badge/?version=latest)](https://dbreport.readthedocs.io/en/latest/?badge=latest)

## Description
This module will generate HTML reports of each view defined in the specified sqlite3 database.

View specific properties, such as a description and friendly name, can be defined in a
`layout.json` file or passed directly as keyword arguments. Each report is a single HTML file
with interactive sorting, filtering, and column visibility, linked to all other reports through
a shared navigation bar.

For the complete documentation, see [Read the Docs](https://dbreport.readthedocs.io/en/latest/index.html)

## Installation

```bash
pip install dbreport
```

For a development (editable) install from source:

```bash
git clone https://github.com/JJCoding01/dbReport.git
cd dbReport
pip install -e .
```

## Quick Start

```python
from dbreport import Report

report = Report(paths={"database": "my.db", "report_dir": "reports/"})
report.generate()   # downloads JS/CSS assets and writes HTML on first run
```

On subsequent runs, use `report.write()` to skip re-downloading static assets:

```python
report.write()
```

Configuration can be passed as keyword arguments, loaded from a JSON layout file, or
both — see [Configuration Precedence](#configuration-precedence) below.

## Generating vs Writing Reports

Three methods cover different stages of the workflow:

| Method | What it does | When to use |
|---|---|---|
| `generate()` | Downloads JS/CSS assets + writes HTML | First run, or after upgrading |
| `write()` | Writes HTML only (assets must already exist) | Routine updates |
| `render()` | Returns `{view_name: html_str}` without writing files | Custom output pipelines |

`generate()` downloads [DataTables](https://datatables.net/) and jQuery from CDN into
`report_dir/static/` the first time it runs. Pass `force=True` to force re-download of
existing assets. Subsequent calls to `write()` skip the network entirely:

```python
# First run — sets up the static folder and writes reports
report.generate()

# Later runs — writes updated HTML only, no network calls
report.write()
```

## Configuration Precedence

Configuration is merged from three layers, highest priority first:

1. **Keyword arguments** passed to `Report(...)` — always win
2. **Layout JSON file** passed as `layout_path` — overrides defaults
3. **Built-in defaults** (`dbreport/templates/layout.json`) — lowest priority

This means you can keep a shared `layout.json` for stable settings (database path,
categories) and override specific keys per run without editing the file:

```python
# layout.json sets the database and categories;
# the kwarg overrides only report_dir for this run
report = Report("layout.json", paths={"report_dir": "reports/today/"})
```

Only `paths.database` is required — all other keys fall back to built-in defaults.

## Layout file

All common parameters can be defined in a layout JSON file passed as the first argument to
`Report`. Parameters include the following.

- `categories` — define dropdown groups in the navigation bar
- `ignore_views` — list of view names (or glob patterns) to exclude from reports
- `titles` — friendly display names for each view
- `paths` — required and optional file paths
- `captions` — per-table captions
- `descriptions` — per-view descriptions shown above the table

### `categories`

Defining categories groups related reports together in the navigation bar. Any view not
assigned to a category is placed in an automatic `Misc` category so every report is always
reachable. A view can appear in multiple categories.

```json
{
  "categories": {
    "First Category": ["view1Name", "view2Name", "view3Name"],
    "Second Category": ["view1Name"]
  }
}
```

View names in each list support glob patterns (`*`, `?`, `[...]`), so you can group views
by naming convention without listing every name individually:

```json
{
  "categories": {
    "Sales":     ["sales_*"],
    "Inventory": ["inv_*", "stock_*"]
  }
}
```

Patterns follow Python's `fnmatch` rules. A pattern that matches no views is silently
ignored; a literal name that doesn't exist in the database produces a warning.

Note: even when view names are specified in the category list, the friendly `title`
(defined below) is what appears in the navigation bar dropdown.

### `ignore_views`

A list of view names to exclude from all reports and navigation menus. Glob patterns are
supported:

```json
{
  "ignore_views": ["_internal_*", "tmp_*"]
}
```

Literal names that don't match any database view produce a warning. Glob patterns that
match nothing are silently ignored.

### `titles`

A mapping from view name to display title. The HTML filename is always the view name, but
the title shown in the report heading and navigation bar uses this value.

```json
{
  "titles": {
    "view1Name": "First View Title",
    "view2Name": "Second View Title"
  }
}
```

### `paths`

| Key | Required | Default | Description |
|---|---|---|---|
| `database` | **Yes** | — | Path to the SQLite `.db` file |
| `report_dir` | No | `reports/` | Directory where HTML reports are written |
| `static` | No | `report_dir/static/` | Directory where JS/CSS assets are stored |
| `template` | No | built-in | Path to a custom Jinja2 template |

Relative paths in a layout file are resolved relative to the layout file's location.

### `descriptions`

A mapping from view name to a longer description shown above the table in the report.

```json
{
  "descriptions": {
    "view1Name": "Detailed description of what this view contains."
  }
}
```

## License
MIT license.

## Credits
- [DataTables](https://datatables.net/) by SpryMedia Ltd — MIT license
- [jQuery](https://jquery.com/) — MIT license
- [jquery-timeago](https://github.com/rmm5t/jquery-timeago) by Ryan McGeary — MIT license
- Test database by [sqlitetutorial.net](https://www.sqlitetutorial.net/sqlite-sample-database/)
