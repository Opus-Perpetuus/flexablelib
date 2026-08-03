from setuptools import setup
from prettyTables.utils import read_json, read_file
import os


setup(
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