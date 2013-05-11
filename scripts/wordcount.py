#!/usr/bin/env python
#encoding=utf-8

from __future__ import unicode_literals
import argparse
import logging
import mwclient
from danmicholoparser import MainText, DanmicholoParseError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description='Prints wordcount for all '
    + 'revisions of a page. May take a long time to run, with high cpu '
    + 'usage, for large pages with many revisions!')
parser.add_argument('page', help='Name of page to check')
parser.add_argument('--lang', default='no', help='Wikipedia language')
args = parser.parse_args()

no = mwclient.Site(args.lang + '.wikipedia.org')

page = no.pages[args.page.decode('utf-8')]

revs = page.revisions(prop='ids|content')

#firstrev = revs.next()
#mt = MainText(firstrev['*'])
#print '----------------------'
#print mt.maintext
#print '----------------------'
#print mt.maintext_alt
#print '----------------------'

#print "Analyzing..."

logger.info('%12s   %s', 'Revision', 'Word count')
for rev in revs:
    mto = MainText(rev['*'])
    words = mto.maintext.split()
    logger.info('%12s   %6d', rev['revid'], len(words))
