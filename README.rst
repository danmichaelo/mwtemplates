================
mwtemplates
================

.. image:: https://travis-ci.org/danmichaelo/mwtemplates.png?branch=master
   :target: https://travis-ci.org/danmichaelo/mwtemplates
.. image:: https://coveralls.io/repos/danmichaelo/mwtemplates/badge.png
   :target: https://coveralls.io/r/danmichaelo/mwtemplates

mwtemplates is a simple wikitext template parser and editor, based on a python rewrite of the mediawiki preprocessorDOM.php. Tested with python 2.6, 2.7, 3.2 and 3.3.

To install requirements:

.. code-block:: console
    
    $ pip install -r requirements.txt

To run tests:

.. code-block:: console
    
    $ pip install -r test_requirements.txt
    $ py.test -x tests --pep8 mwtemplates -v --cov mwtemplates --doctest-modules

Example:

.. code-block:: python

    from mwtemplates import TemplateEditor
    txt = u"""
    {{Infoboks geografi
    | kart = Svalbard_kart1.png
    | land = Norge
    | status = Øygruppe
    | administrasjon = [[Odd Olsen Ingerø]] ''<small>(2009)</small>''
    | administrasjonsnavn = [[Sysselmannen på Svalbard|Sysselmann]]
    | areal = 61022
    | befolkning = 2527
    | befolkningsår = [[2011]]
    | url = www.sysselmannen.svalbard.no
    }}
    """
    te = TemplateEditor(txt)
    te.templates['infoboks geografi'][0].parameters['land'] = 'Russland'
    print te.wikitext()

