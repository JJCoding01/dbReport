"""
Generate HTML reports for the views in a SQLite database.

The :class:`Report` class is the primary interface: instantiate it with a
layout configuration, call :meth:`Report.render` to get HTML strings, or
:meth:`Report.write` to write them directly to disk.
"""

import copy
import json
import os
import sqlite3 as sq3
from datetime import datetime

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


class Report:
    """
    Query a SQLite database and generate sortable, filterable HTML reports.

    Configuration is supplied either as a path to a JSON layout file or as
    keyword arguments whose names match the top-level keys of
    ``dbreport/templates/layout.json`` (e.g. ``paths``, ``categories``,
    ``titles``, ``captions``, ``descriptions``, ``ignore_views``).

    Parameters:
        layout_path (:obj:`str` | :obj:`None`):
            Path to a JSON layout file, or :obj:`None` when using kwargs.
        kwargs: Any keyword argument defined in the layout configuration.

    Raises:
        ValueError: When both ``layout_path`` and keyword arguments are given.
        FileNotFoundError: When the database path does not exist.
    """

    def __init__(self, layout_path=None, **kwargs):
        if layout_path is not None and len(kwargs) > 0:
            raise ValueError("cannot have both layout path and kwargs")
        self.layout = self.__get_layout(layout_path, kwargs)
        self.paths = self.layout["paths"]
        if not os.path.exists(self.paths["database"]):
            msg = f"database '{self.paths['database']}' does not exist"
            raise FileNotFoundError(msg)
        self.cursor = sq3.connect(self.paths["database"]).cursor()
        self.ignore = kwargs.get(
            "ignore_views", self.layout.get("ignore_views", [])
        )

        self.__all_views = None  # initialize, must before self.categories

        self.categories = self.__get_categories()
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(os.path.dirname(self.paths["template"])),
        )
        self.env.filters["has_link"] = lambda value: isinstance(value, tuple)

    def __del__(self):
        """
        Deconstruct method to disconnect/close database connection
        """
        try:
            self.cursor.close()
        except AttributeError:
            pass

    @property
    def categories(self):
        """
        Categories for reports

        The categories is a dictionary defining the menu and the items in the
        menus on each report. This is useful for categorizing the reports
        together.

        Each key is the menu name, how it should appear in the report. The
        values for the key is a list of view names, (note it should be the
        view name, not the alias or title) to be under that heading.
        The name that will appear in the rendered report is the title for
        that report, if one is given.

        A view name can be under multiple menus.

        If a view name does not appear under any menus, it will be
        automatically included in a Misc menu item.
        Unless it is listed in  `ignore`.

        Raises:
            ValueError: when an item is not in `views`
            TypeError: when setting value that is not a :obj:`dict`
            TypeError: when key is not of type :obj:`str`
            Typeerror: when value is not of type :obj:`list`
        """
        return self.__categories

    @categories.setter
    def categories(self, categories):
        """
        Set the categories mapping used to build the navigation bar.

        Parameters:
            categories (:obj:`dict`): Mapping of menu name (:obj:`str`) to a
                list of view names (:obj:`list` of :obj:`str`). Each view name
                must correspond to an existing database view.

        Raises:
            TypeError: When ``categories`` is not a :obj:`dict`.
            TypeError: When any key is not a :obj:`str`.
            TypeError: When any value is not a :obj:`list`.
            ValueError: When any view name in a list does not exist in the
                database.
        """
        if not isinstance(categories, dict):
            raise TypeError("categories must be a dict")

        for category, entries in categories.items():
            # first, check that all categories are strings, and all values
            # are lists
            if not isinstance(category, str):
                raise TypeError("Category must be a str!")
            if not isinstance(entries, list):
                raise TypeError("Category entries must be a list")

            # check that all entries are actually a view. Otherwise it will
            # create a broken link (ie, a link that goes to a non-existent
            for entry in entries:
                if entry not in self.views:
                    raise ValueError(
                        f"given category item '{entry}' does not have a report"
                    )
        self.__categories = categories

    @property
    def ignore(self):
        """
        List of views in database that should not be included in reports

        When setting the `ignore` property, it must be an iterable (:obj:`list`
        or :obj:`tuple`) of view names.

        When a view is listed here, it will not be included in any menu,
        including the `Misc` category.

        Defaults to an empty list

        Raises:
            ValueError: When any item listed is not in `views`
        """
        return self.__ignore

    @ignore.setter
    def ignore(self, values):
        """
        Set the list of view names to exclude from all reports and menus.

        Parameters:
            values (:obj:`list` | :obj:`tuple`): Iterable of view name strings
                to ignore. Every name must correspond to an existing database
                view.

        Raises:
            ValueError: When any name in ``values`` is not a known database
                view.
        """
        for value in values:
            if value not in self.__get_views():
                raise ValueError(
                    f"Cannot update ignore list since '{value}' is not a view"
                )
        self.__ignore = values

    @property
    def paths(self):
        """
        Resolved absolute paths used by this report instance.

        Returns:
            :obj:`dict`: Mapping with at minimum the keys ``database``
            (path to the ``.db`` file), ``report_dir`` (output directory),
            ``template`` (path to the Jinja2 template), ``css_styles``
            (list of CSS file paths), and ``javascript`` (list of JS file
            paths).
        """
        return self.__paths

    @paths.setter
    def paths(self, paths):
        """
        Replace the paths dictionary.

        Parameters:
            paths (:obj:`dict`): New paths mapping. Merges into or replaces
                the current ``paths`` dict used by this instance.
        """
        self.__paths = paths

    def __get_views(self):
        """
        Returns list of all views

        Function to return a list of all views from the database. This does
        not take into account the ignored views.

        Returns
            `obj:list`: list of views from database
        """
        if self.__all_views is not None:
            # the views have already been extracted from the database
            return self.__all_views

        # the views have not been retrieved from the database yet.

        # fetch all database views from the database
        sql = """SELECT name
                 FROM sqlite_master
                 WHERE TYPE = "view"
                 ORDER BY name"""
        data = self.cursor.execute(sql)
        self.__all_views = [view[0] for view in data]
        return self.__all_views

    @property
    def views(self):
        """List of views to be rendered

        This will include all the views defined in the database, without the
        views specified by the `ignore_views` key.

        Returns
            `obj:list`: list of views to be rendered.
        """

        # Filter out any views that are in the ignore list
        return [v for v in self.__get_views() if v not in self.ignore]

    def __set_defaults(self, default_layout, user_layout):
        """
        Merge defaults into user layout, preserving any user-supplied values.

        Recursively walks ``default_layout`` and calls ``setdefault`` on
        ``user_layout`` so that any key not already present is filled in from
        the defaults.

        Parameters:
            default_layout (:obj:`dict`): The reference layout containing all
                required keys and their default values.
            user_layout (:obj:`dict`): The user-supplied layout to be filled
                in. Modified in place.

        Returns:
            :obj:`dict`: ``user_layout`` with all missing keys populated from
            ``default_layout``.
        """

        for k, v in default_layout.items():
            user_layout.setdefault(k, v)
            if isinstance(v, dict):
                self.__set_defaults(v, user_layout[k])
        return user_layout

    @staticmethod
    def __expand_paths(input_paths, base_path):
        """
        Return a copy of the paths dict with non-empty scalar paths resolved to
        absolute paths relative to ``base_path``.

        List values (e.g. ``css_styles``, ``javascript``) are passed through
        unchanged so that relative hrefs embedded in HTML are preserved as-is.

        Parameters:
            input_paths (:obj:`dict`): The ``paths`` dict from a layout file.
            base_path (:obj:`str`): Root directory used to resolve scalar paths.

        Returns:
            :obj:`dict`: Paths dict with scalar paths made absolute.
        """
        layout_paths = {}
        for key, value in input_paths.items():
            if value == "" or isinstance(value, list):
                layout_paths[key] = value
            else:
                layout_paths[key] = os.path.abspath(
                    os.path.join(base_path, value)
                )
        return layout_paths

    def __get_layout(self, user_path, kwargs):
        """
        Build the final layout dict by merging defaults with user config.

        Loads ``dbreport/templates/layout.json`` as the default, then overlays
        either the JSON file at ``user_path`` or the ``kwargs`` dict. All path
        values are expanded to absolute paths relative to each layout file's
        directory.

        Parameters:
            user_path (:obj:`str` | :obj:`None`): Path to the user-supplied
                layout JSON file, or :obj:`None` when kwargs are used.
            kwargs (:obj:`dict`): Keyword arguments passed to
                :meth:`__init__`, used as the user layout when
                ``user_path`` is :obj:`None`.

        Returns:
            :obj:`dict`: Complete layout with all defaults applied and all
            paths resolved to absolute paths.
        """

        # get the base paths that will be used to convert the relative paths
        # in the layout files to absolute
        bases = [os.path.dirname(__file__)]  # default layout base path
        if user_path is not None:
            bases.append(os.path.dirname(user_path))  # user layout base path

            # full path to default and user specified layout files [default, user]
            layout_paths = [
                os.path.join(bases[0], "templates", "layout.json"),
                user_path,
            ]
        else:
            # layout path is None, rely on the keyword arguments
            layout_paths = [os.path.join(bases[0], "templates", "layout.json")]

        layouts = []
        for path in layout_paths:
            with open(path, "r", encoding="utf-8") as f:
                layouts.append(json.load(f))

        if user_path is None:
            layouts.append(kwargs)

        # paths for layouts to be absolute
        for layout, base in zip(layouts, bases):
            layout["paths"] = self.__expand_paths(layout["paths"], base)

        return self.__set_defaults(layouts[0], layouts[1])

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

        # create copy of category parameter to avoid changing input
        updated_categories = copy.deepcopy(categories)

        # create list of all view names that are included with any category.
        # This will be a set, so any duplicates are removed
        categorized_views = set()
        for k in updated_categories.values():
            categorized_views.update(k)

        # iterate over categories and remove any view name that is
        # listed as in the categories
        misc_views = []
        for view in views:
            if view not in categorized_views:
                # this view is not specified in any category, so it should be
                # included in the Misc category
                misc_views.append(view)

        if misc_views:
            # only create misc view category if there are views to add to it
            updated_categories.setdefault("Misc", misc_views)
        return updated_categories

    def __get_categories(self):
        """
        Build the categories dict from layout config, adding a Misc bucket.

        Reads ``self.layout['categories']``, then calls
        :meth:`__add_misc_category` to append any uncategorised views under
        a ``'Misc'`` key.

        Returns:
            :obj:`dict`: Mapping of category name (:obj:`str`) to list of
            view names (:obj:`list` of :obj:`str`) that belong to it.
        """

        cat_list = self.__add_misc_category(
            categories=self.layout["categories"], views=self.views
        )
        return cat_list

    def __get_category_links(self, cat_list):
        """
        Convert a category-to-views mapping into a category-to-links mapping.

        For each category, resolves the display titles for its views and
        builds relative ``./view.html`` href strings, producing the data
        structure consumed by the Jinja2 template's navigation bar.

        Parameters:
            cat_list (:obj:`dict`): Mapping of category name to list of view
                names, as returned by :meth:`__get_categories`.

        Returns:
            :obj:`dict`: Mapping of category name to a tuple of
            ``(titles, paths)`` where ``titles`` is a list of display strings
            and ``paths`` is the corresponding list of relative HTML hrefs.
        """
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

    def __get_data(self, views):
        """
        Query the database and return rows for each requested view.

        Parameters:
            views (:obj:`list` | :obj:`str` | :obj:`None`): View name(s) to
                query. A single string is wrapped in a list. :obj:`None`
                queries all non-ignored views.

        Returns:
            :obj:`dict`: Mapping of view name to a list of row tuples as
            returned by ``cursor.fetchall()``.
        """

        if views is None:
            # views are None, set to use all views
            views = self.views
        elif not isinstance(views, list):
            # make the view a list
            views = [views]

        data = {}
        for view in views:
            sql = f"SELECT * FROM '{view}'"
            results = self.cursor.execute(sql).fetchall()
            data.setdefault(view, results)
        return data

    def __get_columns(self, table_name):
        """
        Return the ordered list of column names for a database view or table.

        Parameters:
            table_name (:obj:`str`): Name of the SQLite view or table.

        Returns:
            :obj:`list` of :obj:`str`: Column names in schema order.
        """
        sql = """PRAGMA table_info("{}")"""
        sql = sql.format(table_name)
        results = self.cursor.execute(sql)
        cols = [col[1] for col in results]
        return cols

    def __get_title(self, view_names):
        """
        Resolve display title(s) for one or more view names.

        Looks up each name in ``layout['titles']``; falls back to the raw
        view name when no override is configured.

        Parameters:
            view_names (:obj:`list` | :obj:`str`): One view name or a list of
                view names to resolve.

        Returns:
            :obj:`str` | :obj:`list` of :obj:`str`: Single title string when
            ``view_names`` is a string; list of title strings when it is a
            list.
        """
        map_names = self.layout["titles"]
        titles = []
        if isinstance(view_names, list):
            for view in view_names:
                titles.append(map_names.get(view, view))
        else:
            titles = map_names.get(view_names, view_names)
        return titles

    def __render_report(self, view_name, data, parse=False):
        """
        Render the Jinja2 template for a single view and return prettified HTML.

        Parameters:
            view_name (:obj:`str`): Name of the database view being rendered.
            data (:obj:`dict`): Mapping of view name to list of row tuples, as
                returned by :meth:`__get_data`.
            parse (:obj:`bool`): When :obj:`True`, passes ``data`` through
                :meth:`parse` before rendering. Defaults to :obj:`False`.

        Returns:
            :obj:`str`: Prettified HTML string for the rendered view.
        """
        css_styles = self.paths["css_styles"]
        javascripts = self.paths["javascript"]
        headers = self.__get_columns(view_name)
        caption = self.layout["captions"].get(view_name, "")
        title = self.__get_title(view_name)
        description = self.layout["descriptions"].get(view_name, "")
        categories = self.__get_category_links(self.categories)

        # Query database for all rows for view given by input
        if parse:  # pragma: no cover
            # call the parse function that may be overloaded
            data = self.parse(data)
        rows = data.get(view_name, [])

        # Get the template for reports and render
        html = self.env.get_template(
            os.path.basename(self.paths["template"])
        ).render(
            title=title,
            description=description,
            categories=categories,
            updated=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            caption=caption,
            css_styles=css_styles,
            javascripts=javascripts,
            headers=headers,
            rows=rows,
        )

        return BeautifulSoup(html, "html.parser").prettify()

    def render(self, views=None, parse=False):
        """
        Renders html for each view in :obj:`views`

        Parameters:
            views (:obj:`list` | :obj:`None`): list of view names to render,
                defaults to :obj:`None`, all views
            parse (:obj:`bool`): whether the parse function is called on
                query results. Defaults to :obj:`False` (don't parse)

        Returns:
            :obj:`dict`: Rendered html of reports

        .. versionchanged:: 0.3.3a1
            returns results; :obj:`parse` default was :obj:`True`
        """
        if isinstance(views, str):
            # views is a single view name and not a list.
            # convert it to a list
            views = [views]
        elif views is None:
            # since no views where explicitly given, render all views
            views = self.views

        reports = {}
        for view in views:
            data = self.__get_data(view)
            html = self.__render_report(view, data, parse)
            reports.setdefault(view, html)
        return reports

    def write(self, report_dir=None, **kwargs):
        """
        Write rendered reports to files

        Parameters:
            report_dir (:obj:`str` | :obj:`None`)
                path where reports are written to defaults to :obj:`None`,
                 which will use the path in the layout.
            kwargs (:obj:`dict`)
                all other keyword arguments are passed directly to the render
                function.

        Returns:
            :obj:`None`: No return value

        Raises:
            :obj:`NotADirectoryError`: When report path does not exist

        .. versionadded:: 0.3.3a1
        """

        if report_dir is None:
            report_dir = self.paths["report_dir"]

        if not os.path.isdir(report_dir):
            raise NotADirectoryError(f"{report_dir} is not a directory")

        rendered_reports = self.render(**kwargs)

        for view, html in rendered_reports.items():
            filename = os.path.join(report_dir, f"{view}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

    def parse(self, data):
        """
        The parse function may be called to intercept data before rendering

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

        This function is useful to filter, format, add hyperlinks, or otherwise
        manipulate raw data queried from database before it gets rendered in
        report.

        To be sure the parse function is called, create a class that inherits
        from the base `Report` class and overload the `parse` function in the
        custom class. Then render the reports with `render(parse=True)`.
        If you try to parse data without overloading the default parse
        function, it will raise a `NotImplementedError`.

        Notes:
            The data format for both :obj:`data` parameter and the returned
            value are defined below.

            - :obj:`keys`: view names where the data was queried from; and the
                filename of the report if using the `write` method.
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
        """

        raise NotImplementedError(
            "parse function must be overloaded before use"
        )
