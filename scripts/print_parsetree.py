#!/usr/bin/env python
#encoding=utf-8

from __future__ import unicode_literals
import mwclient, logging, argparse
from danmicholoparser import DanmicholoParser

parser = argparse.ArgumentParser( description = 'Prints the parsetree used by the MainText module, for debugging cases where the module fails.' )
parser.add_argument('page', help = 'Name of the page to check')
args = parser.parse_args()
pagename = args.page.decode('utf-8') # assume utf-8 terminal

logging.basicConfig(level = logging.DEBUG, format = '%(levelname)7s %(message)s')
log = logging.getLogger()
log.setLevel(logging.DEBUG)

no = mwclient.Site('no.wikipedia.org')
p = no.pages[pagename]
if not p.exists:
    log.error('The page "%s" does not exist', pagename)
else:
    dp = DanmicholoParser(p.edit(readonly=True))
    mtxt = dp.maintext

