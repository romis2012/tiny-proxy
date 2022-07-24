#!/usr/bin/env python
import os
import re
import sys

from setuptools import setup


def get_version():
    here = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(here, 'tiny_proxy', '__init__.py')
    contents = open(filename).read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


def get_long_description():
    with open('README.md', mode='r', encoding='utf8') as f:
        return f.read()


if sys.version_info < (3, 7):
    raise RuntimeError('tiny-proxy requires Python 3.7+')


setup(
    name='tiny_proxy',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=get_version(),
    license='Apache 2',
    url='https://github.com/romis2012/tiny-proxy',
    description='Simple proxy server (SOCKS4(a), SOCKS5(h), HTTP tunnel)',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    packages=[
        'tiny_proxy',
        'tiny_proxy._proxy',
        'tiny_proxy._handlers',
    ],
    keywords='socks socks5 socks4 http proxy server asyncio trio anyio',
    install_requires=[
        'anyio>=3.6.1,<4.0.0',
    ],
)
