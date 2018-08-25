from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()
description = 'Generate html reports of views in a sqlite3 database'
keywords = 'report sqlite sqlite3 html'

setup(
    name='dbreport',
    version='0.1dev',
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
    license='MIT')
