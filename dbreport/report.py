"""
Generate HTML reports for the views in a SQLite database.

The :class:`Report` class is the primary interface: instantiate it with a
layout configuration, call :meth:`Report.render` to get HTML strings, or
:meth:`Report.write` to write them directly to disk.
"""

import copy
import glob
import json
import os
import shutil
import sqlite3 as sq3

from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from .layout import Layout, Paths

_JS_ASSETS = {
    "jquery-timeago": "jquery.timeago.js",
    "multifilter": "multifilter.js",
    "tablesorter": "jquery.tablesorter.js",
}


class Report(Layout):
    """
    Query a SQLite database and generate sortable, filterable HTML reports.

    Configuration is supplied either as a path to a JSON layout file or as
    keyword arguments whose names match the top-level keys of
    ``dbreport/templates/layout.json`` (e.g. ``paths``, ``categories``,
    ``titles``, ``captions``, ``descriptions``, ``ignore_views``).

    Parameters:
        layout_path (:obj:`str` | :obj:`None`):
            Path to a JSON layout file, or :obj:`None` when using kwargs only.
            When provided alongside kwargs, the file is layer 2 and kwargs are
            layer 3 (highest priority).
        kwargs: Any keyword argument defined in the layout configuration.

    Raises:
        FileNotFoundError: When the layout file or database path does not exist.
    """

    def __init__(self, layout_path=None, **kwargs):
        # TODO: Consider warning when entries in categories don't exist in db
        # TODO: Consider warning when ignore_view has views that don't exist in db
        self.layout = self.__get_layout(layout_path, kwargs)

        paths = Paths(**self.layout["paths"])
        if not os.path.exists(paths.database):
            msg = f"database '{paths.database}' does not exist"
            raise FileNotFoundError(msg)
        self.conn = sq3.connect(paths.database)
        self.cursor = self.conn.cursor()
        self._all_views = None
        super().__init__(
            paths=paths,
            ignore_views=self.layout["ignore_views"],
            categories=self.layout["categories"],
            titles=self.layout["titles"],
            captions=self.layout["captions"],
            descriptions=self.layout["descriptions"],
        )
        # Add Misc bucket for any views not covered by the user-specified categories
        self.categories = self.__add_misc_category(
            self.layout["categories"], self.views
        )
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(os.path.dirname(self.paths.template)),
        )
        self.env.filters["has_link"] = lambda value: isinstance(value, tuple)

    def __del__(self):
        """
        Deconstruct method to disconnect/close database connection
        """
        self.close()

    def close(self):
        """Close the database cursor and connection."""
        try:
            self.cursor.close()
            self.conn.close()
            self.cursor = None
            self.conn = None
        except AttributeError:
            pass

    @Layout.ignore_views.setter
    def ignore_views(self, values):
        """
        Set the list of view names to exclude from all reports and menus.

        Parameters:
            values (:obj:`list`): View name strings to ignore. Every name must
                correspond to an existing database view.

        Raises:
            TypeError: When ``values`` is not a list.
            ValueError: When any name in ``values`` is not a known database view.
        """
        if not isinstance(values, list):
            raise TypeError("ignore_views must be a list")
        for value in values:
            if value not in self._get_views():
                raise ValueError(
                    f"Cannot update ignore list since '{value}' is not a view"
                )
        self._ignore = list(values)

    @Layout.categories.setter
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
        Layout.categories.fset(self, categories)
        for entries in categories.values():
            for entry in entries:
                if entry not in self.views:
                    raise ValueError(
                        f"given category item '{entry}' does not have a report"
                    )

    def _get_views(self):
        """
        Returns list of all views

        Function to return a list of all views from the database. This does
        not take into account the ignored views.

        Returns
            `obj:list`: list of views from database
        """
        if self._all_views is not None:
            return self._all_views

        sql = """SELECT name
                 FROM sqlite_master
                 WHERE TYPE = "view"
                 ORDER BY name"""
        data = self.cursor.execute(sql)
        self._all_views = [view[0] for view in data]
        return self._all_views

    @property
    def views(self):
        """List of views to be rendered

        This will include all the views defined in the database, without the
        views specified by the `ignore_views` key.

        Returns
            `obj:list`: list of views to be rendered.
        """
        return [v for v in self._get_views() if v not in self.ignore_views]

    @staticmethod
    def __deep_merge(base, override):
        """
        Return a new dict that is ``base`` deep-merged with ``override``.

        For nested dicts, merges recursively. For all other value types
        (including lists), ``override`` completely replaces ``base``.
        Neither input is mutated.

        Parameters:
            base (:obj:`dict`): The lower-priority dict (defaults).
            override (:obj:`dict`): The higher-priority dict (user values).

        Returns:
            :obj:`dict`: Merged result.
        """
        result = dict(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = Report.__deep_merge(result[key], value)
            else:
                if value is None:
                    # The override is not set, keep the default
                    continue
                result[key] = value
        return result

    def __get_layout(self, user_path, kwargs):
        """
        Build the final layout dict by merging defaults, user file, and kwargs.

        Merging priority (highest to lowest): kwargs > user file > default.
        Paths in each layer are resolved relative to that layer's source
        location before merging.

        Parameters:
            user_path (:obj:`str` | :obj:`None`): Path to the user-supplied
                layout JSON file, or :obj:`None`.
            kwargs (:obj:`dict`): Keyword arguments passed to
                :meth:`__init__`.

        Returns:
            :obj:`dict`: Complete merged layout
        """

        # Layer 1: default layout
        default_base = Path(__file__).parent.absolute()
        with open(
            default_base / "templates" / "static" / "layout.json", "r", encoding="utf-8"
        ) as f:
            result = json.load(f)

        # Resolve the default paths to absolute locations and flatten back to a
        # plain dict so __deep_merge can treat all layers uniformly.
        result["paths"] = Paths(**result["paths"]).set_defaults().as_dict()

        # Layer 2: user file (optional)
        if user_path is not None:
            with open(user_path, "r", encoding="utf-8") as f:
                user_layout = json.load(f)
            result = self.__deep_merge(result, user_layout)

        # Layer 3: kwargs (optional)
        if kwargs:
            result = self.__deep_merge(result, kwargs)

        result["paths"] = Paths(**result["paths"]).as_dict()

        return result

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

    def __get_category_links(self, cat_list):
        """
        Convert a category-to-views mapping into a category-to-links mapping.

        For each category, resolves the display titles for its views and
        builds relative ``./view.html`` href strings, producing the data
        structure consumed by the Jinja2 template's navigation bar.

        Parameters:
            cat_list (:obj:`dict`): Mapping of category name to list of view
                names, as returned by the categories setter.

        Returns:
            :obj:`dict`: Mapping of category name to a tuple of
            ``(titles, paths)`` where ``titles`` is a list of display strings
            and ``paths`` is the corresponding list of relative HTML hrefs.
        """
        categories = {}
        for key, views in cat_list.items():
            titles = self.__get_title(views)
            paths = [os.path.join(".", link + ".html") for link in views]
            categories[key] = (titles, paths)
        return categories

    def __get_data(self, views):
        """
        Query the database and return rows for each requested view.

        Parameters:
            views (:obj:`list`): View names to query.

        Returns:
            :obj:`dict`: Mapping of view name to a list of row tuples as
            returned by ``cursor.fetchall()``.
        """
        data = {}
        for view in views:
            data[view] = self.cursor.execute(f"SELECT * FROM '{view}'").fetchall()
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

        Looks up each name in ``titles``; falls back to the raw view name
        when no override is configured.

        Parameters:
            view_names (:obj:`list` | :obj:`str`): One view name or a list of
                view names to resolve.

        Returns:
            :obj:`str` | :obj:`list` of :obj:`str`: Single title string when
            ``view_names`` is a string; list of title strings when it is a
            list.
        """
        map_names = self.titles
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
        static_dir = self.paths.static
        if static_dir:
            static_name = os.path.basename(static_dir)
            css_files = sorted(glob.glob(os.path.join(static_dir, "css", "*.css")))
            css_styles = [f"{static_name}/css/{os.path.basename(f)}" for f in css_files]
            javascripts = [f"{static_name}/js/{fn}" for fn in _JS_ASSETS.values()]
        else:
            css_styles, javascripts = [], []
        headers = self.__get_columns(view_name)
        caption = self.captions.get(view_name, "")
        title = self.__get_title(view_name)
        description = self.descriptions.get(view_name, "")
        categories = self.__get_category_links(self.categories)

        if parse:  # pragma: no cover
            data = self.parse(data)
        rows = data.get(view_name, [])

        html = self.env.get_template(os.path.basename(self.paths.template)).render(
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
        """
        if isinstance(views, str):
            views = [views]
        elif views is None:
            views = self.views

        data = self.__get_data(views)
        reports = {}
        for view in views:
            reports[view] = self.__render_report(view, data, parse)
        return reports

    def copy_assets(self, path=None):
        """
        Copy the built-in static directory to a new location

        This is useful for initial project setup.

        Call this once to bootstrap the static folder that your rendered reports
        expect. The ``write`` method will not copy assets; use the ``generate``
        method to copy assets and write reports.

        Parameters:
            path: path-like | None: Default None
                Root directory where the assets are to be copied to.
                Default is None, which uses the ``static`` path from the layout
        """
        if path is None:
            path = self.paths.static
        dst = Path(path)

        # get the path to the default base `static` folder
        src = Path(__file__).parent / "templates" / "static"

        # copy over all assets
        shutil.copytree(src, dst, dirs_exist_ok=True)

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
            :obj:`dict`: Rendered html of reports (same as :meth:`render`)

        Raises:
            :obj:`NotADirectoryError`: When report path does not exist
        """

        if report_dir is None:
            report_dir = self.paths.report_dir

        if not os.path.isdir(report_dir):
            raise NotADirectoryError(f"{report_dir} is not a directory")

        rendered_reports = self.render(**kwargs)

        for view, html in rendered_reports.items():
            filename = os.path.join(report_dir, f"{view}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

        return rendered_reports

    def generate(self, report_dir=None, **kwargs):
        """
        Combine the `write()` method and `copy_assets()` methods

        Parameters:
            report_dir (:obj:`str` | :obj:`None`)
                path where reports are written to defaults to :obj:`None`,
                 which will use the path in the layout.
            kwargs (:obj:`dict`)
                all other keyword arguments are passed directly to the render
                function.

        Returns:
            :obj:`dict`: Rendered html of reports (same as :meth:`render`)
        """

        rendered_reports = self.write(report_dir=report_dir, **kwargs)
        self.copy_assets(path=None)

        return rendered_reports

    def parse(self, data):
        """
        Override hook to transform raw query data before rendering.

        Subclass ``Report`` and override this method, then call
        ``render(parse=True)`` to activate it.

        Parameters:
            data (:obj:`dict`): ``{view_name: [row_tuples]}`` as returned by
                the database query. Row elements may be plain values or
                ``(value, href)`` tuples to produce hyperlinks.

        Returns:
            :obj:`dict`: Same structure as ``data``, with values transformed
            as needed for rendering.

        Raises:
            :obj:`NotImplementedError`: Always — must be overridden before use.
        """
        raise NotImplementedError("parse function must be overloaded before use")
