#!/usr/bin/env python
import os
import re
import sys

from setuptools import setup


def get_version():
    here = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(here, 'aiohttp_serve', '__init__.py')
    contents = open(filename).read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


def get_long_description():
    with open('README.md', mode='r', encoding='utf8') as f:
        return f.read()


if sys.version_info < (3, 7):
    raise RuntimeError('aiohttp_serve requires Python 3.7+')


setup(
    name='aiohttp_serve',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=get_version(),
    license='Apache 2',
    url='https://github.com/romis2012/aiohttp-serve',
    description='Multiprocessing based aiohttp application runner',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    packages=[
        'aiohttp_serve',
    ],
    keywords='asyncio aiohttp multiprocessing supervisor',
    install_requires=[
        'aiohttp>=3.7.4',
    ],
)
