#!/usr/bin/env python
#encoding=utf-8

from __future__ import unicode_literals
import sys, difflib, argparse
import mwclient
import logging
from danmicholoparser import DanmicholoParseError, TemplateEditor

parser = argparse.ArgumentParser( description = 'Test if a page if altered by a round-trip through TemplateEditor or not' )
parser.add_argument('page', help='Name of page to check')
parser.add_argument('--output', nargs='?', default='', help='Write output to file')
args = parser.parse_args()

# The code below is from pywikipediabot/userinterfaces/terminal_unix.py
# (C) Pywikipedia bot team, 2003-2012
# Distributed under the terms of the MIT license.
#

unixColors = {
    'default':     chr(27) + '[0m',     # Unix end tag to switch back to default
    'lightblue':   chr(27) + '[94;1m',  # Light Blue start tag
    'lightgreen':  chr(27) + '[92;1m',  # Light Green start tag
    'lightaqua':   chr(27) + '[36;1m',  # Light Aqua start tag
    'lightred':    chr(27) + '[91;1m',  # Light Red start tag
    'lightpurple': chr(27) + '[35;1m',  # Light Purple start tag
    'lightyellow': chr(27) + '[33;1m',  # Light Yellow start tag
}

def printColorized(text):
    lastColor = None
    for key, value in unixColors.iteritems():
        text = text.replace('\03{%s}' % key, value)
    # just to be sure, reset the color
    text += unixColors['default']
    sys.stdout.write(text.encode('utf-8', 'replace'))


def showDiff(oldtext, newtext):
    """
    Output a string showing the differences between oldtext and newtext.
    The differences are highlighted (only on compatible systems) to show which
    changes were made.

    This method is taken from pywikipediabot/pywikibot/__init__.py
    Pywikipedia bot team, 2010-2011
    Distributed under the terms of the MIT license
    """
    # This is probably not portable to non-terminal interfaces....
    # For information on difflib, see http://pydoc.org/2.3/difflib.html
    color = {
        '+': 'lightgreen',
        '-': 'lightred',
    }
    diff = u''
    colors = []
    # This will store the last line beginning with + or -.
    lastline = None
    # For testing purposes only: show original, uncolored diff
    #     for line in difflib.ndiff(oldtext.splitlines(), newtext.splitlines()):
    #         print line
    for line in difflib.ndiff(oldtext.splitlines(), newtext.splitlines()):
        if line.startswith('?'):
            # initialize color vector with None, which means default color
            lastcolors = [None for c in lastline]
            # colorize the + or - sign
            lastcolors[0] = color[lastline[0]]
            # colorize changed parts in red or green
            for i in range(min(len(line), len(lastline))):
                if line[i] != ' ':
                    lastcolors[i] = color[lastline[0]]
            diff += lastline + '\n'
            # append one None (default color) for the newline character
            colors += lastcolors + [None]
        elif lastline:
            diff += lastline + '\n'
            # colorize the + or - sign only
            lastcolors = [None for c in lastline]
            lastcolors[0] = color[lastline[0]]
            colors += lastcolors + [None]
        lastline = None
        if line[0] in ('+', '-'):
            lastline = line
    # there might be one + or - line left that wasn't followed by a ? line.
    if lastline:
        diff += lastline + '\n'
        # colorize the + or - sign only
        lastcolors = [None for c in lastline]
        lastcolors[0] = color[lastline[0]]
        colors += lastcolors + [None]

    result = u''
    lastcolor = None
    for i in range(len(diff)):
        if colors[i] != lastcolor:
            if lastcolor is None:
                result += '\03{%s}' % colors[i]
            else:
                result += '\03{default}'
        lastcolor = colors[i]
        result += diff[i]
    printColorized(result)


logging.basicConfig(format='%(levelname)8s - %(name)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
site = mwclient.Site('no.wikipedia.org')
n = 10
logger.info('Reading page "%s"', args.page)
page = site.pages[args.page]
if page.exists:
    inputtxt = page.edit(readonly = True)
    dp = TemplateEditor(inputtxt)
    try:
        t = dp.templates
        outputtxt = dp.get_wikitext()
        if inputtxt == outputtxt:
            logger.info("Page text passed through TemplateEditor unaltered.")
        else:
            logger.info("Page text was altered during TemplateEditor pass-through. See diff below.")
        showDiff(inputtxt, outputtxt)
        if args.output != '':
            print "Writing output to %s" % args.output
            f = open(args.output, 'w')
            f.write(outputtxt.encode('utf-8'))
            f.close()
    except DanmicholoParseError as e:
        logger.error('Page text could not be parsed: %s', e.msg)
    


else:
    logger.warn('Siden eksisterer ikke')
