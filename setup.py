#!/usr/bin/env python
#encoding=utf-8

#from distutils.core import setup
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


def find_requirements(filename):
    with open(filename, 'r') as f:
        return f.read().splitlines()


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['-x', 'tests', '-v', '--doctest-modules', '--pep8', 'mwtemplates', '--cov', 'mwtemplates']
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
      install_requires=find_requirements('requirements.txt'),
      #tests_require=find_requirements('test_requirements.txt'),
      #cmdclass={'test': PyTest},
      packages=['mwtemplates']
      )
