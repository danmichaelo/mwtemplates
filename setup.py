#!/usr/bin/env python
#encoding=utf-8

#from distutils.core import setup
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(name='mwtemplates',
      version='0.2dev',
      description='MediaWiki template parser and editor',
      author='Dan Michael Heggø',
      author_email='danmichaelo@gmail.com',
      url='https://github.com/danmichaelo/mwtemplates',
      license='MIT',
      keywords='mediawiki',
      packages=['mwtemplates'],
      install_requires=['lxml', 'odict'],
      tests_require=['pytest'],
      cmdclass={'test': PyTest}
      )
