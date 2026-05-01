from dataclasses import dataclass
from pathlib import Path


@dataclass
class Paths:
    """
    File-path settings for a report.

    This matches the structure of ``paths`` sub-object in ``layout.json``.

    Parameters
    ----------
    database : str
        Path to the SQLite ``.db`` file. Required.
    report_dir : str
        Output directory for rendered HTML files.
    static : str
        Directory containing ``css/`` and ``js/`` subdirectories whose files
        are auto-included in each report.
    template : str
        Path to the Jinja2 HTML template. Defaults to
        ``<static>/base.html.j2`` when not explicitly set.
    """

    database: Path = None
    report_dir: Path = None
    static: Path = None
    template: Path = None

    BASE_PATH = Path(__file__).parent

    def __post_init__(self):

        if self.database is not None:
            self.database = Path(self.database)
        if self.report_dir is not None:
            self.report_dir = Path(self.report_dir)
        if self.static is not None:
            self.static = Path(self.static)
        if self.template is not None:
            self.template = Path(self.template)

    def set_defaults(self):
        """
        Set default full paths to the framework default locations.

        Call this method directly to set the defaults.

        Returns
        -------
        Paths
            This instance with defaults applied.
        """
        if self.report_dir is None:
            self.report_dir = Path.cwd() / "reports"

        # set the default static location as inside the `report_dir`. This is
        # done since keeping the static folder inside this framework will cause
        # the css/js files to not be loaded as expected.
        # Note: No default for `static` is set here. The default will be set
        # on report initiation since that's when the final report_dir location
        # will be known. Leave it as a placeholder 'static' location now.

        if not self.template:
            self.template = Path(__file__).parent / "templates" / "base.html.j2"
        return self

    def as_dict(self):
        """Return fields as a plain dict suitable for re-passing to Paths()."""
        return {
            "database": self.database,
            "report_dir": self.report_dir,
            "static": self.static,
            "template": self.template,
        }


class Layout:
    """All configuration parameters for a report, validated at construction.

    Mirrors the structure of ``dbreport/templates/layout.json``: path settings
    are grouped in a :class:`Paths` instance at ``self.paths``, while the
    remaining keys are top-level attributes.

    Parameters
    ----------
    paths : Paths
        File-path settings (database, report_dir, template, static).
    ignore_views : list of str
        View names to exclude from all reports.
    categories : dict
        Maps menu name to list of view names.
    titles : dict
        Per-view display titles.
    captions : dict
        Per-view caption text.
    descriptions : dict
        Per-view description text.
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
        Unless it is listed in `ignore`.

        Raises
        ------
        ValueError
            When an item is not in `views`.
        TypeError
            When setting a value that is not a dict, a key that is not str,
            or a value that is not a list.
        """
        return self._categories

    @categories.setter
    def categories(self, categories):
        """
        Set the categories mapping used to build the navigation bar.

        Parameters
        ----------
        categories : dict
            Mapping of menu name (str) to a list of view names (list of str).

        Raises
        ------
        TypeError
            When ``categories`` is not a dict, any key is not a str, or any
            value is not a list.
        """
        if not isinstance(categories, dict):
            raise TypeError("categories must be a dict")
        for k, v in categories.items():
            if not isinstance(k, str):
                raise TypeError("category keys must be str")
            if not isinstance(v, list):
                raise TypeError("category values must be list")
        self._categories = categories

    @property
    def titles(self):
        """Per-view display title overrides (dict of view name → title string)."""
        return self._titles

    @titles.setter
    def titles(self, value):
        """
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
        if not isinstance(value, dict):
            raise TypeError("titles must be a dict")
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError("titles keys must be str")
            if not isinstance(v, str):
                raise TypeError("titles values must be str")
        self._titles = value

    @property
    def captions(self):
        """Per-view table caption overrides (dict of view name → caption string)."""
        return self._captions

    @captions.setter
    def captions(self, value):
        """
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
        if not isinstance(value, dict):
            raise TypeError("captions must be a dict")
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError("captions keys must be str")
            if not isinstance(v, str):
                raise TypeError("captions values must be str")
        self._captions = value

    @property
    def descriptions(self):
        """Per-view description overrides (dict of view name → description string)."""
        return self._descriptions

    @descriptions.setter
    def descriptions(self, value):
        """
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
        if not isinstance(value, dict):
            raise TypeError("descriptions must be a dict")
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError("descriptions keys must be str")
            if not isinstance(v, str):
                raise TypeError("descriptions values must be str")
        self._descriptions = value
