"""
This module will will generate HTML reports for the views in a sqlite database.
"""

import json
import os
import sqlite3 as sq3
from datetime import datetime

from jinja2 import Environment, FileSystemLoader


class Report(object):
    """
    The Report will handle querying the database and generating the reports

    Parameters:
        layout_path (:obj:`str`): path to the layout file

    """

    def __init__(self, layout_path):
        self.path = layout_path
        self.layout = self.__get_layout(layout_path)
        self.paths = self.layout["paths"]
        self.cursor = sq3.connect(self.paths["database"]).cursor()
        self.categories = self.__get_categories()
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(os.path.dirname(self.paths["template"])),
        )
        self.env.filters["has_link"] = lambda value: isinstance(value, tuple)

    def __set_defaults(self, default_layout, user_layout=None):
        """
        Set the values in the user_layout to override the defaults

        This will recursively navigate through the default layout dictionary
        to ensure the user specified layout has all the required keys.

        :return: dict: user_layout
        :param default_layout: dict: default layout
        :param user_layout: dict: user layout (defaults to None)
        """
        if user_layout is None:
            user_layout = {}

        for k, v in default_layout.items():
            user_layout.setdefault(k, v)
            if isinstance(v, dict):
                self.__set_defaults(v, user_layout[k])
        return user_layout

    @staticmethod
    def __expand_paths(input_paths, base_path):
        """
        Expand the paths attribute of the layout file to use absolute paths

        :input
        :param input_paths: dict: paths given in a layout file
        :param base_path: str: root path to be pre-pended to each of the paths

        :return:
        layout_paths: dict: drop in replacement for the layout['paths'] key
                            with relative paths converted to absolute paths
        """
        layout_paths = {}
        for key in input_paths:
            if input_paths[key] == "":
                layout_paths.setdefault(key, "")
                continue

            if isinstance(input_paths[key], list):
                layout_paths[key] = []
                for k, path in enumerate(input_paths[key]):
                    dirs = path.split("/")
                    layout_paths[key].append(
                        os.path.abspath(os.path.join(base_path, *dirs))
                    )
                continue

            dirs = input_paths[key].split("/")
            full_path = os.path.abspath(os.path.join(base_path, *dirs))

            layout_paths.setdefault(key, full_path)
            # layout_paths.setdefault(key, paths[key])
            if os.path.isdir(full_path) and key != "report_dir":
                files = []
                for file in os.listdir(full_path):
                    files.append(os.path.join(full_path, file))
                if len(files) == 0:
                    layout_paths[key] = full_path
                else:
                    layout_paths[key] = files
        return layout_paths

    def __get_layout(self, user_path):
        """
        Return the user layout, with all defaults set, given the path to the
        user-specified layout file.
        """

        # get the base paths that will be used to convert the relative paths
        # in the layout files to absolute
        bases = [
            os.path.dirname(__file__),  # default layout base path
            os.path.dirname(self.path),
        ]  # user layout base path

        # full path to default and user specified layout files [default, user]
        layout_paths = [
            os.path.join(bases[0], "templates", "layout.json"),
            user_path,
        ]

        layouts = []
        for path in layout_paths:
            with open(path, "r") as f:
                layouts.append(json.load(f))

        # paths for layouts to be absolute
        for layout, base in zip(layouts, bases):
            layout["paths"] = self.__expand_paths(layout["paths"], base)

        return self.__set_defaults(*layouts)

    @staticmethod
    def __add_misc_category(categories, views):
        """
        Return a dictionary with the categories defined in the layout
        file, as well as an additional 'Misc' category that contains
        any view, not listed in the ignore_views list, that is not
        specified in another category. This will ensure that there will
        be a convenient way to access all reports from the navigation
        bar in each report.
        """

        # iterate over categories and remove any view name that is
        # listed as in the categories
        for category in categories:
            for view in categories[category]:
                if view in views:
                    views.remove(view)
        categories.setdefault("Misc", views)
        return categories

    def __get_categories(self):
        """
        Given the category name and list of view names, return
        a dictionary with category name and list of relative paths to
        the report for that view
        """

        cat_list = self.__add_misc_category(
            categories=self.layout["categories"], views=self.__get_views()
        )

        categories = {}
        for key in cat_list:
            paths = []
            titles = self.__get_title(cat_list[key])
            for link in cat_list[key]:
                # Note all the reports are all in the same folder
                path = os.path.join(".", link + ".html")
                paths.append(path)
            categories.setdefault(key, (titles, paths))

        return categories

    def __get_views(self):
        """return a list of view names from database"""
        filename = self.paths["sql"][0]
        with open(filename, "r") as f:
            sql = f.read()
        data = self.cursor.execute(sql)
        views = [view[0] for view in data]

        # Remove any views that are in the ignore list in the layout
        # file
        ignore_views = self.layout["ignore_views"]
        for ignore_view in ignore_views:
            if ignore_view in views:
                views.remove(ignore_view)
        return views

    def __get_data(self, views=None):
        """get the data for the view(s) given"""

        if views is None:
            # views are None, set to use all views
            views = self.__get_views()
        elif not isinstance(views, list):
            # make the view a list
            views = [views]

        data = {}
        for view in views:
            sql = "SELECT * FROM '{}'".format(view)
            results = self.cursor.execute(sql)
            rows = [result for result in results]
            data.setdefault(view, rows)

        return data

    def __get_columns(self, table_name):
        """return a list of columns for the given table"""
        sql = """PRAGMA table_info("{}")"""
        sql = sql.format(table_name)
        c = self.cursor.execute(sql)
        cols = [col[1] for col in c]
        return cols

    def __get_title(self, view_names):
        """return the name/title to be used as the page title"""
        map_names = self.layout["titles"]
        titles = []
        if isinstance(view_names, list):
            for view in view_names:
                titles.append(map_names.get(view, view))
        else:
            titles = map_names.get(view_names, view_names)
        return titles

    def __render_report(self, view_name, data, parse=True):
        """render an output report"""
        # Set up basic constants for this report
        update = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        report_dir = self.paths["report_dir"]
        css_styles = self.paths["css_styles"]
        js = self.paths["javascript"]
        headers = self.__get_columns(view_name)
        caption = self.layout["captions"].get(view_name, "")
        title = self.__get_title(view_name)
        description = self.layout["descriptions"].get(view_name, "")
        categories = self.categories

        # Query database for all rows for view given by input
        # data = self.__get_all_data()
        if parse:
            # call the parse function that may be overloaded
            data = self.parse(data)

        rows = [row for row in data[view_name]]

        # Get the template for reports and render
        temp = self.env.get_template(os.path.basename(self.paths["template"]))
        html = temp.render(
            title=title,
            description=description,
            categories=categories,
            updated=update,
            caption=caption,
            css_styles=css_styles,
            javascripts=js,
            headers=headers,
            rows=rows,
        )

        # Write rendered template to file in reports directory
        filename = "{}.html".format(view_name)
        with open(os.path.join(report_dir, filename), "w") as f:
            f.write(html)

    def render(self, views=None, parse=True):
        """
        renders a report of each of the view names in :obj:`views`

        Parameters:
            views (:obj:`list` | :obj:`None`): list of view names to to render,
                defaults to :obj:`None`, all views
            parse (:obj:`bool`): whether the parse function is called on
                query results.

        Returns:
            :obj:`None`: No return value

        """
        if isinstance(views, str):
            # views is a single view name and not a list.
            # convert it to a list
            views = [views]
        elif views is None:
            # since no views where explicitly given, render all views
            views = self.__get_views()

        for view in views:
            data = self.__get_data(view)
            self.__render_report(view, data, parse)

    def parse(self, data):
        """
        The parse function may be called to intercept data before rendering

        This is useful to filter, format, add hyperlinks, or otherwise
        manipulate raw data queried from database before it gets rendered in
        report.

        To be sure the parse function is called, inherit from the base `Report`
        class and overload the `parse` function in the custom class. Then
        render the reports with `render(parse=True)`. If you try to parse data
        without overloading the default parse function, it will raise a
        `NotImplimentedError`.

        Notes:
            The data format for both :obj:`data` parameter and the returned
            value are defined below.

            - :obj:`key`: view names where the data was queried from
            - :obj:`values`: list of tuples, each tuple is a row of data
               - (:obj:`list`): list of rows, with each row defined as a tuple
               - (:obj:`tuple`): each element in :obj:`values` is a tuple.
                                 The elements of the tuple are the values from
                                 the database, and/or the values that will be
                                 shown in the report.

            .. note::
                The elements of each row must be a single item (:obj:`str`,
                :obj:`bool`, :obj:`int`, etc) or a tuple in the form
                (:obj:`value`, :obj:`href`), where :obj:`href` is where the
                generated hyperlink for that value is directed to.

        Parameters:
            data (:obj:`dict`): data as queried from database.
                            The keys are view names from database, and
                            values are a list of queried results.

        Returns:
            :obj:`dict`: data as it should be rendered by report.
                     The keys are view names as used in `layout` file, and
                     values are a list of results to be included in reports.

        Raises:
            :obj:`NotImplementedError`: When the default parse function is used.
                This must be overloaded by a custom parse function before use.

        """

        raise NotImplementedError('parse function must be overloaded before use')
