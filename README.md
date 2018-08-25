#Readme

##Description
This module will generate HTML reports of each view defined in the specified sqlite3 database.

View specific properties, such as a description, friendly name, etc can be predefined and the report generator will use these when making the report of the view.

###Layout file
All common parameters must be defined in a layout file. This will allow the report be rerun against the same database multiple times to keep reports up-to-date.

Things that are defined in the layout file include

 - `categories` define the nav-bar in the reports
 - `titles` define a friendly name for each view. If not defined the view name will be used
 - `paths` required paths to database, css files, where reports are saved, etc
 - `captions` predetermined caption for each table
 - `descriptions` pre-set description of the view that will be included with the report

This script comes with a default `layout.json` file. Any parameters that are not defined in the user specified layout file, will use the parameters specified in the default layout file.

##License
MIT license.

##Credits
 - jQuery plugin `timeago` by Ryan McGeary [www.timeago.yarp.com](https://timeago.yarp.com/) licensed under the MIT license
 - jQuery plugin `tablesorter` by Christian Bach [github.com/christianbach/tablesorter](https://github.com/christianbach/tablesorter) licensed under the MIT license
 - jQuery plugin `multifilter` by Tommy Palmer [github.com/tommyp/multifilter](https://github.com/tommyp/multifilter) licensed under the MIT license

##Notes
This is a project that I needed for a personal project, and is currently under active development. I hope you get some use out of it. Suggestions for improvements are welcome.
