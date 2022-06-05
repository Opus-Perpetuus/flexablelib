from distutils.core import setup
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
  classifiers=[
    'Development Status :: 4 - Beta',      
    'Intended Audience :: Developers',      
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9'
  ],
  entry_points={
    'console_scripts': []
  }
)