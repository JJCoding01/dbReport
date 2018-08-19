#Readme

##Description
This module will generate a series of reports of the views defined
in the specified database.

View specific properties, such as a description, friendly name, etc can
be pre-defined and the report generator will use these when generating the report that view.

###Layout file
All common parameters must be defined in a layout file. This will allow
the report be rerun against the same database multiple times to keep reports up-to-date.

Things that are defined in the layout file include

 - `categories` define the nav-bar in the reports
 - `titles` define a friendly name for each view. If not defined the view name will be used
 - `paths` required paths to database, css files, where reports are saved, etc
 - `captions` predetermined caption for each table
 - `descriptions` pre-set description of the view that will be included with the report


##Usage Examples

##Report Examples

##Installation Instructions

##Liscense

##Credits
Add proper credits for js plug-ins
 - timeago
 - tablesorter
 - multicolomn filter plugin
