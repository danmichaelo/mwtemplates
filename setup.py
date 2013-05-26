#!/usr/bin/env python
#encoding=utf-8

# Bootstrap setuptools
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(name='mwtemplates',
      version='0.2dev',
      description='MediaWiki template parser and editor',
      long_description=README,
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
      ],
      keywords='mediawiki wikipedia',
      author='Dan Michael Heggø',
      author_email='danmichaelo@gmail.com',
      url='https://github.com/danmichaelo/mwtemplates',
      license='MIT',
      packages=['mwtemplates'],
      install_requires=['lxml']
      )
