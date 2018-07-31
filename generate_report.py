import sqlite3 as sq3
# import settings
import os
from jinja2 import Template
from datetime import datetime
import json


class Report(object):
    """Object that will define a report"""

    def __init__(self, layout_path):
        with open(layout_path, 'r') as f:
            self.layout = json.loads(f.read())
        self.paths = self.layout['paths']
        self.cursor = sq3.connect(self.paths['database']).cursor()
        self.categories = self.get_categries()
        # self.title_map = self.layout['titles']
        # print(self.title_map)

    @staticmethod
    def read_file(filename):
        """return the sql for the given file"""
        with open(filename, 'r') as f:
            return f.read()

    def get_views(self):
        """return a list of view names from database"""
        filename = os.path.join(self.paths['SQL'], 'get_views.sql')
        data = self.get_data(filename)
        views = [view[0] for view in data]
        return views

    def get_data(self, filename):
        """return cursor object of data"""
        sql = self.read_file(filename)
        return self.cursor.execute(sql)

    def get_all_data(self):
        """return a dictionary containing all the data for all views"""
        views = self.get_views()
        data = {}
        for view in views:
            sql = '''SELECT * FROM {}'''.format(view)
            results = self.cursor.execute(sql)
            rows = [result for result in results]
            data.setdefault(view, rows)
        return data

    def get_columns(self, table_name):
        """return a list of columns for the given table"""
        sql = '''PRAGMA table_info("{}")'''
        sql = sql.format(table_name)
        c = self.cursor.execute(sql)
        cols = []
        cols = [col[1] for col in c]
        return cols

    def get_title(self, view_names):
        """return the name/title to be used as the page title"""
        map_names = self.layout['titles']
        titles = []
        if type(view_names) is list:
            for view in view_names:
                titles.append(map_names.get(view, view))
        else:
            titles =map_names.get(view_names, view_names)

        return titles

    def get_categries(self):
        """
        Given the category name and list of view names, return
        a dictionary with category name and list of relative paths to
        the report for that view
        """
        cat_list = self.layout['categories']
        categories = {}
        report = self.paths['reports']
        report = os.path.abspath(report)
        for key in cat_list:
            paths = []
            titles = self.get_title(cat_list[key])
            for link in cat_list[key]:
                path = os.path.join(report, link + '.html')
                paths.append(path)
                val = [titles, paths]
            categories.setdefault(key, val)

        return categories
    def render_report(self, view_name):
        """render an output report"""
        template = self.paths['template']
        report_dir = self.paths['reports']
        css_style = self.paths['css_styles']
        js = self.paths['javascript']

        temp = self.read_file(template)
        T = Template(temp)
        update = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        data = self.get_all_data()
        rows = [row for row in data[view_name]]

        headers = self.get_columns(view_name)
        # print(headers)
        caption = self.layout['captions'][view_name]
        title = self.get_title(view_name)
        description = self.layout['descriptions'][view_name]
        categories = self.categories
        html = T.render(title=title,
                        description=description,
                        categories=categories,
                        updated=update,
                        caption=caption,
                        css_style=css_style,
                        js=js,
                        headers=headers,
                        rows=rows)
        filename = '{}.html'.format(view_name)
        with open(os.path.join(report_dir, filename), 'w') as f:
            f.write(html)

    def render_all(self):
        """render all templates"""
        views = self.get_views()
        for view in views:
            self.render_report(view)


def main():
    # path = settings.DATABASE_PATH
    path = os.path.join('reports', 'templates', 'layout.json')
    R = Report(path)
    R.render_all()
    # R.get_categries()
    # v = R.get_views()
    # print(v)
    # t = R.get_title(v)
    # print(t)
    # t = R.get_title('DriveModelOptions')
    # print(t)
    # c = R.get_categries()
    # print(c)
    # h = R.get_columns('ListChains')
    # R.render_report('ListChains')
    # data = R.get_all_data()
    # R.render_report()

    # for key in data:
    #     print(key)
    #     for row in data[key]:
    #         print('\ttest1{}'.format(row))


if __name__ == '__main__':

    main()
