from setuptools import setup, Extension
from prettyTables.utils import read_json, read_file
import os


# Accelerated text measurement. Marked optional so a machine with no compiler,
# or a platform with no published wheel, still gets a working install -- the
# package falls back to the pure-Python implementation in text_width.py.
speedups = Extension(
  'prettyTables._speedups',
  sources=['prettyTables/_speedups.c'],
  optional=True,
)


setup(
  ext_modules=[speedups],
  name = 'prettyTables',         
  packages = ['prettyTables'],   
  version = read_json(f'.{os.sep}package.json')['version'],      
  description = 'Tables to print in console',   
  long_description=read_file('README.md'),
  long_description_content_type='text/markdown',
  author = 'Benjamin Ramirez',                   
  author_email = 'chilerito12@gmail.com',      
  url = 'https://github.com/Kyostenas/prettyTables',   
  license='MIT',        
  download_url = '',    
  keywords = ['console', 'graphics'],   
  install_requires=[],
  # The base install stays dependency-free. Readers and writers that need a
  # third-party library are opt-in: pip install prettyTables[pandas,excel]
  extras_require={
    'pandas': ['pandas>=1.0'],
    'excel': ['openpyxl>=3.0'],
    'html': ['lxml>=4.0'],
    'all': ['pandas>=1.0', 'openpyxl>=3.0', 'lxml>=4.0'],
  },
  python_requires='>=3.8',
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
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