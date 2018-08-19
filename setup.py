import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()
description = 'Script to generate reports from views in sqlite3 database'
keywords = 'report sqlite sqlite3 html'

setuptools.setup(
    name='dbreport',
    version='0.1dev',
    description=description,
    long_description=long_description,
    author='Joseph Contreras',
    author_email='26684136+JosephJContreras@users.noreply.github.com',
    url='',
    packages=setuptools.find_packages(),
    keywords=keywords,
    license='MIT')
