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
import warnings

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

    Parameters
    ----------
    layout_path : str or None
        Path to a JSON layout file, or None when using kwargs only. When
        provided alongside kwargs, the file is layer 2 and kwargs are layer 3
        (highest priority).
    **kwargs
        Any keyword argument defined in the layout configuration.

    Raises
    ------
    FileNotFoundError
        When the layout file or database path does not exist.
    """

    def __init__(self, layout_path=None, **kwargs):
        # TODO: Consider warning when entries in categories don't exist in db
        # TODO: Consider warning when ignore_view has views that don't exist in db
        self.layout = self.__get_layout(layout_path, **kwargs)

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

        # Add `has_link` boolean variable into the template.
        # The rendering template with use this during processing
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

        Parameters
        ----------
        values : list
            View name strings to ignore. Every name must correspond to an
            existing database view.

        Raises
        ------
        TypeError
            When ``values`` is not a list.
        ValueError
            When any name in ``values`` is not a known database view.
        """

        # Call the `ignore_views` setter method for `Layout` and apply any
        # logic or tests that the parent has.
        Layout.ignore_views.fset(self, values)

        # find all views that are ignored but do not exist
        ignore_dne = []
        for value in values:
            if value not in self._get_views():
                ignore_dne.append(value)

        # warn for any views that are listed to be ignored, but do not actually
        # have a view.
        if ignore_dne:
            # there are views that are ignored that do not exist
            views = ", ".join(f"{v!r}" for v in ignore_dne)
            msg = f"The following views were ignored but do not exist: {views}"
            warnings.warn(msg, UserWarning)

    @Layout.categories.setter
    def categories(self, categories_):
        """
        Set the categories mapping used to build the navigation bar.

        Parameters
        ----------
        categories_ : dict
            Mapping of menu name (str) to a list of view names (list of str).
            Each view name must correspond to an existing database view.

        Raises
        ------
        TypeError
            When ``categories`` is not a dict, any key is not a str, or any
            value is not a list.
        ValueError
            When any view name in a list does not exist in the database.
        """
        # Call the `categories` setter method for `Layout` and apply any
        # logic or tests that the parent has.
        Layout.categories.fset(self, categories_)

        # find all views listed in a category that does not exist and build a
        # cleaned copy that omits them so they don't produce broken nav links
        existing_views = set(self.views)
        view_dne = set()
        cleaned = {}
        for key, entries in categories_.items():
            valid = [e for e in entries if e in existing_views]
            for entry in entries:
                if entry not in existing_views:
                    view_dne.add(f"{key}>{entry}")
            if valid:
                cleaned[key] = valid

        if view_dne:
            views = ", ".join(f"{v!r}" for v in view_dne)
            msg = f"The following categories were listed but do not exist: {views}"
            warnings.warn(msg, UserWarning)
            self._categories = cleaned

    @Layout.titles.setter
    def titles(self, value):
        """
        Set per-view display titles, warning for any key that is not a known view

        Parameters
        ----------
        value : dict
            Mapping of view name (str) to display title (str).

        Raises
        ------
        TypeError
            When ``value`` is not a dict, any key is not a str, or any value
            is not a str.
        """
        Layout.titles.fset(self, value)
        dne = [k for k in value if k not in self._get_views()]
        if dne:
            views = ", ".join(f"{v!r}" for v in dne)
            warnings.warn(
                f"The following titles were listed but do not exist: {views}",
                UserWarning,
            )

    @Layout.captions.setter
    def captions(self, value):
        """
        Set per-view captions, warning for any key that is not a known view

        Parameters
        ----------
        value : dict
            Mapping of view name (str) to caption text (str).

        Raises
        ------
        TypeError
            When ``value`` is not a dict, any key is not a str, or any value
            is not a str.
        """
        Layout.captions.fset(self, value)
        dne = [k for k in value if k not in self._get_views()]
        if dne:
            views = ", ".join(f"{v!r}" for v in dne)
            warnings.warn(
                f"The following captions were listed but do not exist: {views}",
                UserWarning,
            )

    @Layout.descriptions.setter
    def descriptions(self, value):
        """
        Set per-view descriptions, warning for any key that is not a known view

        Parameters
        ----------
        value : dict
            Mapping of view name (str) to description text (str).

        Raises
        ------
        TypeError
            When ``value`` is not a dict, any key is not a str, or any value
            is not a str.
        """
        Layout.descriptions.fset(self, value)
        dne = [k for k in value if k not in self._get_views()]
        if dne:
            views = ", ".join(f"{v!r}" for v in dne)
            warnings.warn(
                f"The following descriptions were listed but do not exist: {views}",
                UserWarning,
            )

    def _get_views(self):
        """
        Return a list of all views from the database.

        Does not account for ignored views.

        Returns
        -------
        list
            View names from the database.
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
        """
        List of views to be rendered.

        All database views excluding those specified by ``ignore_views``.

        Returns
        -------
        list
            View names to be rendered.
        """
        return [v for v in self._get_views() if v not in self.ignore_views]

    @staticmethod
    def __deep_merge(base, override):
        """
        Return a new dict that is ``base`` deep-merged with ``override``.

        For nested dicts, merges recursively. For all other value types
        (including lists), ``override`` completely replaces ``base``.
        Neither input is mutated.

        Parameters
        ----------
        base : dict
            The lower-priority dict (defaults).
        override : dict
            The higher-priority dict (user values).

        Returns
        -------
        dict
            Merged result.
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

    def __get_layout(self, user_path, **kwargs):
        """
        Build the final layout dict by merging defaults, user file, and kwargs.

        Merging priority (highest to lowest): kwargs > user file > default.
        Paths in each layer are resolved relative to that layer's source
        location before merging.

        Parameters
        ----------
        user_path : str or None
            Path to the user-supplied layout JSON file, or None.
        kwargs : dict
            Keyword arguments passed to :meth:`__init__`.

        Returns
        -------
        dict
            Complete merged layout.
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

        Parameters
        ----------
        cat_list : dict
            Mapping of category name to list of view names, as returned by
            the categories setter.

        Returns
        -------
        dict
            Mapping of category name to a tuple of ``(titles, paths)`` where
            ``titles`` is a list of display strings and ``paths`` is the
            corresponding list of relative HTML hrefs.
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

        Parameters
        ----------
        views : list
            View names to query.

        Returns
        -------
        dict
            Mapping of view name to a list of row tuples as returned by
            ``cursor.fetchall()``.
        """
        data = {}
        for view in views:
            data[view] = self.cursor.execute(f"SELECT * FROM '{view}'").fetchall()
        return data

    def __get_columns(self, table_name):
        """
        Return the ordered list of column names for a database view or table.

        Parameters
        ----------
        table_name : str
            Name of the SQLite view or table.

        Returns
        -------
        list of str
            Column names in schema order.
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

        Parameters
        ----------
        view_names : list or str
            One view name or a list of view names to resolve.

        Returns
        -------
        str or list of str
            Single title string when ``view_names`` is a string; list of
            title strings when it is a list.
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

        Parameters
        ----------
        view_name : str
            Name of the database view being rendered.
        data : dict
            Mapping of view name to list of row tuples, as returned by
            :meth:`__get_data`.
        parse : bool, optional
            When True, passes ``data`` through :meth:`parse` before rendering.
            Default is False.

        Returns
        -------
        str
            Prettified HTML string for the rendered view.
        """
        static_dir = self.paths.static
        if static_dir:
            static_name = os.path.basename(static_dir)
            css_files = sorted(glob.glob(os.path.join(static_dir, "css", "*.css")))

            # note, get css paths relative to the static folder. Browsers do
            # not load absolute windows paths
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
        Render HTML for each view in ``views``.

        Parameters
        ----------
        views : list or None, optional
            View names to render. Default is None, which renders all views.
        parse : bool, optional
            Whether the parse function is called on query results.
            Default is False.

        Returns
        -------
        dict
            Rendered HTML of reports.
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
        Copy the built-in static directory to a new location.

        This is useful for initial project setup. Call this once to bootstrap
        the static folder that your rendered reports expect. The ``write``
        method will not copy assets; use the ``generate`` method to copy
        assets and write reports.

        Parameters
        ----------
        path : path-like or None, optional
            Root directory where the assets are to be copied to. Default is
            None, which uses the ``static`` path from the layout.
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
        Write rendered reports to files.

        Parameters
        ----------
        report_dir : str or None, optional
            Path where reports are written to. Default is None, which uses the
            path in the layout.
        **kwargs
            All other keyword arguments are passed directly to :meth:`render`.

        Returns
        -------
        dict
            Rendered HTML of reports (same as :meth:`render`).

        Raises
        ------
        NotADirectoryError
            When the report path does not exist.
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
        Combine the :meth:`write` and :meth:`copy_assets` methods.

        Parameters
        ----------
        report_dir : str or None, optional
            Path where reports are written to. Default is None, which uses the
            path in the layout.
        **kwargs
            All other keyword arguments are passed directly to :meth:`render`.

        Returns
        -------
        dict
            Rendered HTML of reports (same as :meth:`render`).
        """

        if report_dir is None:
            report_dir = self.paths.report_dir

        os.makedirs(report_dir, exist_ok=True)

        self.copy_assets(path=None)
        rendered_reports = self.write(report_dir=report_dir, **kwargs)

        return rendered_reports

    def parse(self, data):
        """
        Override hook to transform raw query data before rendering.

        Subclass ``Report`` and override this method, then call
        ``render(parse=True)`` to activate it.

        Parameters
        ----------
        data : dict
            ``{view_name: [row_tuples]}`` as returned by the database query.
            Row elements may be plain values or ``(value, href)`` tuples to
            produce hyperlinks.

        Returns
        -------
        dict
            Same structure as ``data``, with values transformed as needed for
            rendering.

        Raises
        ------
        NotImplementedError
            Always — must be overridden before use.
        """
        raise NotImplementedError("parse function must be overloaded before use")
