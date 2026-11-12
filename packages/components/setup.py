import os
import re

from setuptools import setup

HERE = os.path.dirname(os.path.abspath(__file__))


def version():
    with open(os.path.join(HERE, 'flexablelib_components', '__init__.py')) as f:
        return re.search(r"__version__ = '([^']+)'", f.read()).group(1)


def readme():
    with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
        return f.read()


setup(
    name='flexablelib-components',
    version=version(),
    description='Interactive terminal components for flexablelib: inputs, '
                'dates, tables, forms, menus, tabs, dialogs and more.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Benjamin Ramirez',
    author_email='chilerito12@gmail.com',
    url='https://github.com/Opus-Perpetuus/flexablelib',
    license='MIT',
    packages=['flexablelib_components'],
    package_data={'flexablelib_components': ['py.typed']},
    install_requires=['flexablelib>=' + version(),
                      'flexablelib-tui>=' + version()],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Terminals',
        'Topic :: Software Development :: User Interfaces',
    ],
)
