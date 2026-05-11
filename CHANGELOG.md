# Change Log

## [0.4.0] 11-May-2026

### Breaking Changes
- `setup.py` removed in favour of `pyproject.toml`; install with `pip install .` as before.
- Git submodules (`tablesorter`, `multifilter`, `jquery-timeago`) replaced by DataTables.
  DataTables assets are downloaded from their original source when the end user generates
  reports, rather than being bundled with the package.

### New Features
- **DataTables integration** - sorting and column filtering now powered by DataTables
  (replaces tablesorter + multifilter). Filter boxes show placeholder text.
- **Layered option handling** - `Report` now merges config from multiple sources
  (layout JSON file, constructor kwargs, call-site kwargs) in a consistent priority order.
- **layout options support globbing** - view name globbing is now allowed
- **`generate()` method** - single call that writes reports *and* copies static assets.
- **`dbreport/util/` module** - new `views.py` and `triggers.py` helpers for
  extracting and importing SQLite views and triggers.
- **`dbreport/layout.py`** - layout/config logic extracted into its own module with
  `layout.Paths` dataclass and improved default handling.

### Improvements
- Monolithic `dbreport/dbreport.py` refactored into `dbreport/report.py` (Report class)
  and `dbreport/layout.py` (config/path handling).
- Static assets (CSS, JS) relocated to `dbreport/templates/static/` and copied to the
  report output directory at generation time; paths in rendered HTML are now relative.
- `write()` now returns the report directory path.
- Doc-strings rewritten in NumPy format throughout.
- DB connection handling made more robust (explicit close/disconnect).
- Missing-view warnings replace errors for `titles`, `captions`, `descriptions`,
  `categories`, and `ignore_views` keys.

## v0.3.3a2
 - Corrected bug where views listed in the `ignore_views` key from layout file
   were still getting rendered

## v0.3.3a1
 - Added tests and added CI on Travis
 - Added `Report.write` to write rendered output to files

 **Backwards Incompatible Changes**
 - Updated `Report.render` method to return dictionary of rendered reports
 rather than write output directly to output files
 - Changed default parameter `parse` for `Report.render` to `False` (was `True`)
