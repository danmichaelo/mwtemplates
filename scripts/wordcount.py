#!/usr/bin/env python
#encoding=utf-8

from __future__ import unicode_literals
import argparse 
import mwclient
from danmicholoparser import DanmicholoParser, DanmicholoParseError

parser = argparse.ArgumentParser( description = 'Prints wordcount for all revisions of a page. ' \
    + 'May take a long time to run, with high cpu usage, for large pages with many revisions!' )
parser.add_argument('page', help='Name of page to check')
args = parser.parse_args()

no = mwclient.Site('no.wikipedia.org')

page = no.pages[args.page]

print "Getting revision texts..."
revs = [[int(r['revid']),r['*']] for r in page.revisions(prop='ids|content')]

#revs.sort(key = lambda x: x[0], reverse = True)

print "Analyzing..."
dprevs = []
for r in revs:
    try:
        x = DanmicholoParser(r[1]).maintext
        dprevs.append([r[0],x])
        print r[0],len(x.split())
    except DanmicholoParseError as e:
        print r[0], e.msg

#for r in dprevs:


