#!/usr/bin/env python
# encoding=utf-8
from __future__ import print_function

import os
import sys

try:
    from setuptools import setup
    from setuptools.command.test import test as TestCommand
except ImportError:
    print("This package requires 'setuptools' to be installed.")
    sys.exit(1)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = '-v --pep8 tests mwtemplates'

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst'), encoding='utf-8').read()  # Python 3
except TypeError:
    README = open(os.path.join(here, 'README.rst')).read()  # Python 2

setup(name='mwtemplates',
      version='0.3.4',
      description='MediaWiki template parser and editor',
      long_description=README,
      classifiers=[
          'Topic :: Text Processing :: Markup',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='mediawiki wikipedia',
      author='Dan Michael Heggø',
      author_email='danmichaelo@gmail.com',
      url='https://github.com/danmichaelo/mwtemplates',
      license='MIT',
      packages=['mwtemplates'],
      install_requires=['lxml', 'six'],
      cmdclass={'test': PyTest},
      tests_require=['pytest-pep8', 'pytest-cache', 'pytest', 'mock']
      )
