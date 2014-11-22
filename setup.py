#!/usr/bin/env python
# encoding=utf-8

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(name='mwtemplates',
      version='0.3.3dev',
      description='MediaWiki template parser and editor',
      long_description=README,
      classifiers=[
          'Topic :: Text Processing :: Markup',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
      ],
      keywords='mediawiki wikipedia',
      author='Dan Michael Heggø',
      author_email='danmichaelo@gmail.com',
      url='https://github.com/danmichaelo/mwtemplates',
      license='MIT',
      packages=['mwtemplates'],
      install_requires=['lxml', 'six']
      )
