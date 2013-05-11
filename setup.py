#!/usr/bin/env python
#encoding=utf-8

#from distutils.core import setup
from setuptools import setup

setup(name='mwtemplates',
    version='0.1',
    description='MediaWiki template parser and editor',
    author='Dan Michael Heggø',
    author_email='danmichaelo@gmail.com',
    url='https://github.com/danmichaelo/mwtemplates',
    license='MIT',
    keywords='mediawiki',
    packages=['mwtemplates'],
    setup_requires=['nose>=1.0'],
    test_suite = 'nose.collector',
    install_requires = ['lxml', 'odict']
)

