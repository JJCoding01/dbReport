Layout Configuration
====================

The layout file defines how the reports are generated, the database that should
be queried, aliases, and other options for rendering. It can also be used to
pass parameters to the parse function to process data before report is
rendered.

This is a JSON file that defines the following keys. Each JSON key is described
below.

categories
**********
The categories is a dictionary defining the menu and the items in the menus
on each report. This is useful for categorizing the reports together.

Each key is the menu name, how it should appear in the report. The values
for the key is a list of view names, (note it should be the view name, not the
alias or title) to be under that heading. The name that will appear in the
rendered report is the title for that report, if one is given.

A view name can be under multiple menus.

If a view name does not appear under any menus, it will be automatically
included in a `Misc` menu item. Unless it is listed in the ``ignore_views`` key.

ignore_views
************
List of view names to be ignored. These will not be included in any of the
menus, including the `Misc` menu. These must correspond to the keys in the data
returned by the parse function.

titles
******
A dictionary of aliases for the reports. The keys are the view names from the
database, (keys in dictionary returned by parse function) and the values are
the alias that should be used. This alias will be used as the report title,
and the menu item text.

paths
*****
Paths given to the report. They are given as key-value pairs, where the
required keys are listed below.

  * **database**: path to the database to be queried
  * **report_dir**: path to directory where reports are saved. This must be a directory. Defaults to ``reports``
  * **template**: path to html template. Defaults to ``templates/base.html.j2``
  * **css_styles**: directory to css files. All css files in directory are included. Defaults to ``templates/css``
  * **sql**: defaults to ``templates/sql``,
  * **javascript**: list to paths javascript plugins to be included in reports
      * ``"templates/javascript/jquery-timeago/jquery.timeago.js"``
      * ``"templates/javascript/multifilter/multifilter.js"``
      * ``"templates/javascript/tablesorter/jquery.tablesorter.js"``

The paths listed may be absolute or relative to the calling function.


captions
********
Dictionary of key value pairs that define the table caption for each report.

The keys match the report name (view name, not alias) and the value is the
caption as it should appear in the report.

Defaults to :obj:`None` (no caption)

descriptions
************
Dictionary of key value pairs that define a description (introductory text)
for each report.

The keys match the report name (view name, not alias) and the value is the
description text as it should appear in the report.

Defaults to :obj:`None` (no description).

