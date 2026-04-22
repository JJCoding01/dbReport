from dataclasses import dataclass, field


@dataclass
class Paths:
    """
    File-path settings for a report

    This matches the structure of ``paths`` sub-object in ``layout.json``.

    Parameters:
        database (:obj:`str`): Path to the SQLite ``.db`` file. Required.
        report_dir (:obj:`str`): Output directory for rendered HTML files.
        template (:obj:`str`): Path to the Jinja2 HTML template.
        css_styles (:obj:`list` of :obj:`str`): CSS file hrefs for each report.
        javascript (:obj:`list` of :obj:`str`): JS file hrefs for each report.
    """

    database: str
    report_dir: str = "reports"
    template: str = ""
    css_styles: list = field(default_factory=list)
    javascript: list = field(default_factory=list)


class Layout:
    """All configuration parameters for a report, validated at construction.

    Mirrors the structure of ``dbreport/templates/layout.json``: path settings
    are grouped in a :class:`Paths` instance at ``self.paths``, while the
    remaining keys are top-level attributes.

    Parameters:
        paths (:class:`Paths`): File-path settings (database, report_dir, template,
            css_styles, javascript).
        ignore_views (:obj:`list` of :obj:`str`): View names to exclude from
            all reports.
        categories (:obj:`dict`): Maps menu name to list of view names.
        titles (:obj:`dict`): Per-view display titles.
        captions (:obj:`dict`): Per-view caption text.
        descriptions (:obj:`dict`): Per-view description text.
    """

    def __init__(
        self,
        paths,
        ignore_views=None,
        categories=None,
        titles=None,
        captions=None,
        descriptions=None,
    ):
        self.paths = paths
        self.ignore_views = ignore_views if ignore_views is not None else []
        self.categories = categories if categories is not None else {}
        self.titles = titles if titles is not None else {}
        self.captions = captions if captions is not None else {}
        self.descriptions = descriptions if descriptions is not None else {}

    @property
    def ignore_views(self):
        """
        List of view names excluded from all reports and menus.
        """
        return self._ignore

    @ignore_views.setter
    def ignore_views(self, values):
        if not isinstance(values, list):
            raise TypeError("ignore_views must be a list")
        self._ignore = list(values)

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
        return self._categories

    @categories.setter
    def categories(self, categories):
        """
        Set the categories mapping used to build the navigation bar.

        Parameters:
            categories (:obj:`dict`): Mapping of menu name (:obj:`str`) to a
                list of view names (:obj:`list` of :obj:`str`).

        Raises:
            TypeError: When ``categories`` is not a :obj:`dict`.
            TypeError: When any key is not a :obj:`str`.
            TypeError: When any value is not a :obj:`list`.
        """
        if not isinstance(categories, dict):
            raise TypeError("categories must be a dict")
        for k, v in categories.items():
            if not isinstance(k, str):
                raise TypeError("category keys must be str")
            if not isinstance(v, list):
                raise TypeError("category values must be list")
        self._categories = categories
