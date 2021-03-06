mwtemplates
==================

.. image:: http://img.shields.io/travis/danmichaelo/mwtemplates.svg?style=flat
   :target: https://travis-ci.org/danmichaelo/mwtemplates
   :alt: Build status

.. image:: http://img.shields.io/coveralls/danmichaelo/mwtemplates.svg?style=flat
   :target: https://coveralls.io/r/danmichaelo/mwtemplates
   :alt: Test coverage

.. image:: https://img.shields.io/pypi/v/mwtemplates.svg?style=flat
   :target: https://pypi.python.org/pypi/mwtemplates/
   :alt: Latest version

.. image:: https://img.shields.io/pypi/pyversions/mwtemplates.svg?style=flat
   :target: https://pypi.python.org/pypi/mwtemplates/
   :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/dm/mwtemplates.svg?style=flat
   :target: https://pypi.python.org/pypi/mwtemplates/
   :alt: Downloads

mwtemplates is a MediaWiki wikitext template parser and editor, based on a Python rewrite of the MediaWiki preprocessorDOM.php.
Tested with python 2.7, 3.3, 3.4, 3.5


Installation
-------------------

The package is on `PyPI <https://pypi.python.org/pypi/mwtemplates>`_, so you can install it
using `pip`, `easy_install` or similar:

.. code-block:: console

   $ pip install -U mwtemplates

Or you can grab the latest zip from `releases <https://github.com/danmichaelo/mwtemplates/releases>`_.

Introduction
------------

Let's start by importing `TemplateEditor` and giving it some wikitext to eat:

.. code-block:: python

    >>> from mwtemplates import TemplateEditor
    >>> txt = u"""{{Infobox cheese
    ... | name = Mozzarella
    ... | protein = 7
    ... }}
    ... Mozzarella is a cheese…{{tr}}"""
    >>> te = TemplateEditor(txt)

First, we can see what templates the editor found in the text:

.. code-block:: python

    >>> te.templates
    [<Template:"Infobox cheese" at line 2>, <Template:"Tr" at line 6>]

Each template is an instance of a `Template` class. Also notice that template names are normalized by upper-casing the first character. Now, we can try investigating the `Infobox cheese` template:

.. code-block:: python

    >>> te.templates['Infobox cheese']
    [<Template:"Infobox cheese" at line 2>]

Since there can be several instances of the same template, an array is always returned, and so we need to ask for `te.templates['Infobox cheese'][0]` to get the actual `Template`. To get the parameters:

.. code-block:: python

    >>> te.templates['Infobox cheese'][0].parameters
    <Parameters: name="Mozzarella", protein="10">

Let's say we want to change the value of the `protein` parameter from 10 to 7. We then use
the `wikitext()` method to return our new wikitext:

.. code-block:: python

    >>> te.templates['Infobox cheese'][0].parameters['protein'] = 7
    >>> print te.wikitext()
    {{Infobox cheese
    | name = Mozzarella
    | protein = 10
    }}
    Mozzarella is a cheese…{{tr}}

Notice that formatting is preserved. We could now go and add a new parameter like so:

.. code-block:: python

    >>> te.templates['Infobox cheese'][0].parameters['fat'] = 25
    >>> print te.wikitext()
    {{Infobox cheese
    | name = Mozzarella
    | protein = 7
    | fat = 25
    }}
    Mozzarella is a cheese…{{tr}}

To remove a template argument:

.. code-block:: python

    from mwtemplates import TemplateEditor
    te = TemplateEditor(u"Hello {{mytpl | a=2 | b=3 | c=4 }} world")
    te.templates['mytpl'].parameters.remove('b')

To remove the first instance of a template:

.. code-block:: python

    from mwtemplates import TemplateEditor
    te = TemplateEditor(u"Hello {{mytpl}} world {{mytpl}}")
    te.templates['mytpl'][0].remove()


Known issues
----------------------------------------------

The parser doesn't handle empty `<nowiki/>` tags. It will raise a
`mwtemplates.NowikiError` error if feeded a page having one, so it's
a good idea to handle those:

.. code-block:: python

    >>> from mwtemplates import TemplateEditor, NowikiError
    >>> try:
    >>>     te = TemplateEditor(txt)
    >>> except NowikiError:
    >>>     print('Page contains <nowiki/> tags, skipping.')


Usage with mwclient to edit pages on Wikipedia
----------------------------------------------

Updating a page on Wikipedia using `mwclient <https://github.com/mwclient/mwclient>`_

.. code-block:: python

   from mwclient import Site
   from mwtemplates import TemplateEditor

   site = Site('en.wikipedia.org')
   site.login('USERNAME', 'PASSWORD')
   page = site.pages['SOME_PAGE']
   te = TemplateEditor(page.text())
   if 'SOME_TEMPLATE' in page.templates:
      tpl = te.templates['SOME_TEMPLATE'][0]
      tpl.parameters['test'] = 'Hello'
   page.save(te.wikitext(), summary='...')


Contributing
------------

Pull requests are very welcome. Please run tests before submitting:

.. code-block:: console

    $ python setup.py test
