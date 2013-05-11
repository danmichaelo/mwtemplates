mwtemplates
================

[![Build Status](https://travis-ci.org/danmichaelo/mwtemplates.png?branch=master)](https://travis-ci.org/danmichaelo/mwtemplates)

Simple wikitext template parser and editor, based on a python rewrite of preprocessorDOM.php.

Tested with Python 2.7

```
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

```
