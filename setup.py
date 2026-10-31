from setuptools import setup, Extension
from flexablelib.utils import read_json, read_file
import os


# Accelerated text measurement. Marked optional so a machine with no compiler,
# or a platform with no published wheel, still gets a working install -- the
# package falls back to the pure-Python implementation in text_width.py.
speedups = Extension(
  'flexablelib._speedups',
  sources=['flexablelib/_speedups.c'],
  optional=True,
)


setup(
  ext_modules=[speedups],
  name = 'flexablelib',         
  packages = ['flexablelib'],
  package_data = {'flexablelib': ['py.typed']},
  include_package_data = True,
  version = read_json(f'.{os.sep}package.json')['version'],      
  description = ('Fast, dependency-free terminal tables for Python: 56 border '
                 'styles, ANSI colors, cell merges, decimal alignment, '
                 'width fitting, and CSV/Markdown/HTML/Excel/LaTeX I/O.'),
  long_description=read_file('README.md'),
  long_description_content_type='text/markdown',
  author = 'Benjamin Ramirez',                   
  author_email = 'chilerito12@gmail.com',      
  url = 'https://github.com/Opus-Perpetuus/flexablelib',   
  license='MIT',        
  project_urls = {
    'Documentation': 'https://github.com/Opus-Perpetuus/flexablelib#readme',
    'Source': 'https://github.com/Opus-Perpetuus/flexablelib',
    'Issues': 'https://github.com/Opus-Perpetuus/flexablelib/issues',
    'Changelog': 'https://github.com/Opus-Perpetuus/flexablelib/blob/main/CHANGELOG.md',
    'Releases': 'https://github.com/Opus-Perpetuus/flexablelib/releases',
  },
  keywords = [
    'table', 'tables', 'terminal', 'console', 'cli', 'ascii-table',
    'pretty-print', 'prettytable', 'tabulate', 'tabular-data', 'ansi',
    'ansi-colors', 'unicode', 'box-drawing', 'markdown', 'html', 'csv',
    'excel', 'latex', 'formatting',
  ],
  install_requires=[],
  # The base install stays dependency-free. Readers and writers that need a
  # third-party library are opt-in: pip install flexablelib[pandas,excel]
  extras_require={
    'pandas': ['pandas>=1.0'],
    'excel': ['openpyxl>=3.0'],
    'html': ['lxml>=4.0'],
    'all': ['pandas>=1.0', 'openpyxl>=3.0', 'lxml>=4.0'],
  },
  python_requires='>=3.8',
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: C',
    'Topic :: Terminals',
    'Topic :: Text Processing',
    'Topic :: Text Processing :: Markup',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities',
    'Typing :: Typed',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Programming Language :: Python :: 3.14',
    'Programming Language :: Python :: 3 :: Only'
  ],
  entry_points={
    'console_scripts': []
  }
)