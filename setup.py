from distutils.core import setup

def readfile(filename):
  with open(filename, 'r+') as f:
    return f.read()
  
setup(
  name = 'prettyTables',         
  packages = ['prettyTables'],   
  version = '1.0.0',      
  description = 'Tables to print in console',   
  long_description=readfile('README.md'),
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