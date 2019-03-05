from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()
description = 'Generate html reports of views in a sqlite3 database'
keywords = 'report sqlite sqlite3 html'

paths = ['*',  # html template and CSS files
         'SQL/*',  # directory for SQL files
         'css/*.css',  # all css files
         'javascript/multifilter/*.js',  # multifilter js plugin
         'javascript/tablesorter/*.js',  # tablesorter js plugin
         'javascript/jquery-timeago/*.js',  # timeago js plugin
         ]
paths = ['templates/' + p for p in paths]

setup(
    name='dbreport',
    version='0.3.0dev',
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Joseph Contreras',
    author_email='26684136+JosephJContreras@users.noreply.github.com',
    url='https://github.com/JosephJContreras/dbreport.git',
    packages=find_packages(),
    classifiers=['Development Status::3 - Alpha'],
    keywords=keywords,
    install_requires=['jinja2'],
    entry_points={'console_scripts': ['report=dbreport:cli']},
    package_data={'dbreport': paths,
                  '': ['License.txt']},
    include_package_data=True,
    license='MIT')
