from distutils.core import setup
setup(
  name = 'prettyTables',         
  packages = ['prettyTables'],   
  version = '0.1',      
  license='MIT',        
  description = 'All sorts of tables and graphics for console (for now just tables) ',   
  author = 'Benjamin Ramirez',                   
  author_email = 'chilerito12@gmail.com',      
  url = 'https://github.com/Kyostenas/prettyGraphics',   
  download_url = 'https://github.com/Kyostenas/prettyTables/archive/v0.1-beta.1.tar.gz',    
  keywords = ['console', 'graphics'],   
  install_requires=[ 
      'nltk'
      ],
  classifiers=[
    'Development Status :: Beta',      
    'Intended Audience :: Developers',      
    'Topic :: Software Development :: Console tools',
    'License :: OSI Approved :: MIT License',   
    'Programming Language :: Python :: 3',      
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9'
  ],
)