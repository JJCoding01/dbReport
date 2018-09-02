import sqlite3 as sq3
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import json


class Report(object):
    """Object that will define a report"""

    def __init__(self, layout_path):
        self.path = layout_path
        with open(layout_path, 'r') as f:
            user_layout = json.loads(f.read())
        self.layout = self.__set_default_settings(user_layout)
        self.paths = self.layout['paths']
        self.cursor = sq3.connect(self.paths['database']).cursor()
        self.categories = self.__get_categories()
        self.env = Environment(
            trim_blocks=True, lstrip_blocks=True,
            loader=FileSystemLoader(self.paths['template_dir']))

    def __set_default_settings(self, user_layout, default_layout=None):
        """
        Set the default settings that are not set in the user
        layout file
        """

        def set_default_paths():
            """
            Get default paths. If the path is in the specified layout
            file, that path should be used, otherwise fall back and use
            the default
            """
            # Read the default layout file provided by the package
            package_path = os.path.dirname(__file__)
            path = os.path.join(package_path, 'templates', 'layout.json')
            with open(path, 'r') as f:
                def_layout = json.loads(f.read())

            # expand paths in default layout to be absolute
            template_dir = os.path.join(package_path,
                                        def_layout['paths']['template_dir'][0])
            def_layout['paths']['template_dir'] = template_dir

            # iterate over path lists and update them be an absolute path
            # pointing to the package defaults
            for p in ['css_styles', 'javascript', 'sql']:
                paths = []
                for path in def_layout['paths'][p]:
                    paths.append(os.path.join(template_dir, path))
                def_layout['paths'][p] = paths
            return def_layout

        if default_layout is None:
            # Set the paths to the layout file distributed
            # with the package
            default_layout = set_default_paths()
        # Iterate over keys and set to default if not specified in user
        # layout file
        for key in default_layout:
            user_layout.setdefault(key, default_layout[key])
            if isinstance(default_layout[key], dict):
                user_layout[key] = self.__set_default_settings(
                    user_layout[key], default_layout[key])

        return user_layout

    def __add_misc_category(self, categories, views):
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
        categories.setdefault('Misc', views)
        return categories

    def __get_categories(self):
        """
        Given the category name and list of view names, return
        a dictionary with category name and list of relative paths to
        the report for that view
        """

        categories = self.layout['categories']
        cat_list = self.__add_misc_category(
            categories=self.layout['categories'],
            views=self.__get_views())

        categories = {}
        for key in cat_list:
            paths = []
            titles = self.__get_title(cat_list[key])
            for link in cat_list[key]:
                # Note all the reports are all in the same folder
                path = os.path.join('.', link + '.html')
                paths.append(path)
                val = (titles, paths)
            categories.setdefault(key, val)

        return categories

    def __get_views(self):
        """return a list of view names from database"""
        filename = os.path.join(self.paths['sql'][0], 'get_views.sql')
        with open(filename, 'r') as f:
            sql = f.read()
        data = self.cursor.execute(sql)
        views = [view[0] for view in data]

        # Remove any views that are in the ignore list in the layout
        # file
        ignore_views = self.layout['ignore_views']
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
            sql = 'SELECT * FROM {}'.format(view)
            results = self.cursor.execute(sql)
            rows = [result for result in results]
            data.setdefault(view, rows)

        return data

    def __get_columns(self, table_name):
        """return a list of columns for the given table"""
        sql = '''PRAGMA table_info("{}")'''
        sql = sql.format(table_name)
        c = self.cursor.execute(sql)
        cols = [col[1] for col in c]
        return cols

    def __get_title(self, view_names):
        """return the name/title to be used as the page title"""
        map_names = self.layout['titles']
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
        report_dir = self.paths['report_dir']
        css_styles = self.paths['css_styles']
        js = self.paths['javascript']
        headers = self.__get_columns(view_name)
        caption = self.layout['captions'].get(view_name, "")
        title = self.__get_title(view_name)
        description = self.layout['descriptions'].get(view_name, "")
        categories = self.categories

        # Query database for all rows for view given by input
        # data = self.__get_all_data()
        if parse:
            # call the parse function that may be overloaded
            data = self.parse(data)

        rows = [row for row in data[view_name]]

        # Get the template for reports and render
        temp = self.env.get_template(self.paths['template'])
        html = temp.render(title=title,
                           description=description,
                           categories=categories,
                           updated=update,
                           caption=caption,
                           css_styles=css_styles,
                           javascripts=js,
                           headers=headers,
                           rows=rows)

        # Write rendered template to file in reports directory
        filename = '{}.html'.format(view_name)
        with open(os.path.join(report_dir, filename), 'w') as f:
            f.write(html)

    def render(self, views=None, parse=True):
        """
        Primary method for rendering method. This will call the
        appropriate internal methods to render the reports.
        This function will allow for the following options

            1. Render specified views only
            2. Render all views
            3. Enable/disable parsing data
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

        return len(views)

    def parse(self, data):
        """
        This parse method will be called before rendering the report.
        It should be used to verify, clean up, or add hyper-links to
        data and return a data dictionary with keys as the view name,
        and a tuple for each row.
        """
        return data
