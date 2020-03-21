Readme
=======

[![Build Status](https://travis-ci.org/josephjcontreras/dbReport.svg?branch=master)](https://travis-ci.org/josephjcontreras/dbReport)
[![Coverage Status](https://coveralls.io/repos/github/josephjcontreras/dbReport/badge.svg?branch=master)](https://coveralls.io/github/josephjcontreras/dbReport?branch=master)
[![Documentation Status](https://readthedocs.org/projects/dbreport/badge/?version=latest)](https://dbreport.readthedocs.io/en/latest/?badge=latest)

## Description
This module will generate HTML reports of each view defined in the specified sqlite3 database.

View specific properties, such as a description and friendly name can be predefined and in a `layout.json` file.

Each report is a single file, with links to all other reports through the navigation bar.

For the complete documentation, see [Read the Docs](https://dbreport.readthedocs.io/en/latest/index.html)

## Installation

Since this module has several sub-modules, to clone, perform the following steps
to clone it with all the sub-modules populated. 

```bash
>> git clone https://github.com/josephjcontreras/dbreport.git
>> cd dbReport
>> git submodule init
>> git submodule update
```

For further details about submodules, refer to the [git documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules).

Once cloned, `dbReport` can be installed by adding a link to the cloned repository using
by activating the virtual environment, navigating to the root project folder and running 
`pip install -e .` .

## Layout file
All common parameters must be defined in a layout file. Parameters that are defined include the
following.

 - `categories` define the nav-bar in the reports
 - `ignore_views` list of view names to exclude from reports
 - `titles` define a friendly name for each view. If not defined the view name will be used
 - `paths` required paths to database, css files, where reports are saved, etc
 - `captions` predetermined caption for each table
 - `descriptions` pre-set description of the view that will be included with the report

#### `categories`
Defining categories is not required, but is helpful to group similar reports together in the
navigation bar in each report. If a view is not given a specific category, it is assigned to a
`Misc` category on the navigation bar. This ensures there is an easy way to access any report, from
any other report. Each view can be a member of multiple categories, or none at all. By not defining
a category, it is implied that it is part of the `Misc` category (unless the
view name is in `ignore_views`).

To define a category, enter a list of view names with a key of the category name.
See layout snippet below
```json
{
  "categories": {"First Category": ["view1Name", "view2Name", "view3Name"],
               "Second Category": ["view1Name"]}
}
```
This will add two dropdown menus in the navigation bar of each report.

 - `First Category` will be the first dropdown, and will contain links to reports for `view1Name`, `view2Name`, and `view3Name`
 - `Second Category` will be the second dropdown, and will contain one link to `view1Name`

Note that the even through the view names are specified in the category list, the view title
(defined below) will show up in the dropdown menu in the navigation bar.


#### `titles`
Defining titles allows giving meaningful names to reports without changing the view name. This is a
map from view name to report title. The filename of the report will always be the view name, but
the report title, and the report name that shows up in the navigation bar, will be the title.

for example

```json
{
"titles": {
            "view1Name": "First View Title",
            "view2Name": "Second View Title",
            "view3Name": "Third View Title"
    }
}
```

#### `paths`
The `paths` key in the layout file defines all paths required for running the project. These 
paths may be absolute paths or paths relative to the layout file.

The defined paths include:

 - `database` Path to database file
 - `template` path to the base `HTML/jinja2` template that all reports will be created from
 - `css_styles` path to directory containing CSS files (all files in this directory will be included in reports)
 - `javascript` a list of Javascript plugins to be connected to the reports
 
 By default, the following plugins are included
  + [timeago](https://timeago.yarp.com/) for showing a relative time for when the report was created
  + [tablesorter](https://github.com/christianbach/tablesorter) for quickly sorting the table by any column
  + [multifilter](https://github.com/tommyp/multifilter) for filtering the table based inputs for each column
 - `sql` the directory where sql files are stored
 - `report_dir` directory where generated reports are to be stored

  See below for the default paths set as the defaults.
```json
{
"paths": {
  "database": "",
  "template": "templates/base.html.j2",
  "css_styles": "templates/css",
  "javascript": [
    "templates/javascript/jquery-timeago/jquery.timeago.js",
    "templates/javascript/multifilter/multifilter.js",
    "templates/javascript/tablesorter/jquery.tablesorter.js"
  ],
  "sql": "templates/sql",
  "report_dir": "reports",
  "search_paths": ""
    }
}
```

#### `descriptions`
Descriptions are a dictionary defining an extended description of the view that will be included on the report.


This script comes with a default `layout.json` file. Any parameters that are not defined in the user specified layout file, will use the parameters specified in the default layout file.

## License
MIT license.

## Credits
 - jQuery plugin `timeago` by Ryan McGeary [www.timeago.yarp.com](https://timeago.yarp.com/) licensed under the MIT license
 - jQuery plugin `tablesorter` by Christian Bach [github.com/christianbach/tablesorter](https://github.com/christianbach/tablesorter) licensed under the MIT license
 - jQuery plugin `multifilter` by Tommy Palmer [github.com/tommyp/multifilter](https://github.com/tommyp/multifilter) licensed under the MIT license
 - Test database by [sqlitetutorial.net](https://www.sqlitetutorial.net/sqlite-sample-database/)

## Notes
This is a project that I needed for a personal project, and is currently under active development. I hope you get some use out of it. Suggestions for improvements are welcome.
