.. dbReport documentation master file, created by
   sphinx-quickstart on Sun Sep  8 09:42:53 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

##########################
dbReport's Documentation
##########################

The dbReport package will generate HTML reports from a sqlite database.
It uses views defined in the database to collect the data for the reports, and
a JSON file to configure how the reports are generated and related to
each other. The project can be found on `github <https://github.com/josephjcontreras/dbReport/>`_


.. toctree::
   :maxdepth: 1

   layout
   dbreport
   license

.. contents::

Installation
------------
This project is not hosted on PyPi, so to install it will require building the
project from source.

Since this module has several sub-modules (js plugins), to clone, perform the
following steps to clone it with all the sub-modules populated.

  .. code-block:: shell

    >> git clone https://github.com/josephjcontreras/dbreport.git
    >> cd dbReport
    >> git submodule init
    >> git submodule update


For further details about submodules, refer to the `git documentation <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`_.

Once cloned, install the requirements by running
``pip install -r requirements.txt`` or ``pip install -r requirements-dev.txt``,
depending on how you will use the project.

Example Setup
-------------
Once *dbReport* has been installed, it can be used to start generating reports.


.. code-block:: json

    {
    "paths": {
        "database": ".\\test-database.db",
        "report_dir": ".\\reports"
        }
    }

For simple cases that do not require processing of data queried from the
database, the reports can be rendered as shown.

.. code-block:: python

    def main():
        report = Report('layout.json')
        report.render(parse=False)

In other cases where the ``parse`` function is required, create a python class
that inherits from the ``dbreport.Report`` class. This will allow the parse
method to be overloaded and changed.

.. code-block:: python

      from dbreport import Report

      class myCustomReport(Report):
          def __init__(self, layout_path):
              super().__init__(layout_path=layout_path)

          def parse(self, data):
              """
              This custom parse function will be called on the data

              See documentation for more details.
              """

              # for this case, we're just going to print the data to
              # show that it is working
              print(data)

              # be sure to return the data
              return data


      def main():
          # use this function to instantiate the class and generate reports
          report = myCustomReport('layout.json')
          report.render()


After running these examples, there will be an html report for each view
defined in ``test-database.db``.
