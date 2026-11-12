import os
import re

from setuptools import Extension, setup

HERE = os.path.dirname(os.path.abspath(__file__))


def version():
    with open(os.path.join(HERE, 'flexablelib_speedups', '__init__.py')) as f:
        return re.search(r"__version__ = '([^']+)'", f.read()).group(1)


def readme():
    with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
        return f.read()


setup(
    name='flexablelib-speedups',
    version=version(),
    description='Optional C acceleration of terminal frame drawing for '
                'flexablelib (cut, pad, borders, frame diffs).',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Benjamin Ramirez',
    author_email='chilerito12@gmail.com',
    url='https://github.com/Opus-Perpetuus/flexablelib',
    license='MIT',
    packages=['flexablelib_speedups'],
    ext_modules=[Extension('flexablelib_speedups._frames',
                           sources=['flexablelib_speedups/_frames.c'],
                           depends=['flexablelib_speedups/_width_tables.h'],
                           # No compiler: the install still succeeds and
                           # flexablelib keeps its pure-Python frame code.
                           optional=True)],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: C',
        'Programming Language :: Python :: 3',
        'Topic :: Terminals',
    ],
)
