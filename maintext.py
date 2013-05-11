# encoding=utf-8
#encoding=utf-8
"""
DanmicholoParser
Copyright (c) 2012-2013 Dan Michael O. Heggø

Simple wikitext template parser and editor
"""

from __future__ import unicode_literals
import re
from bs4 import BeautifulSoup
from bs4 import NavigableString

from lxml.html import fromstring
from lxml.etree import tostring

import logging
logger = logging.getLogger(__name__)

from danmicholoparser.dperrors import DanmicholoParseError
from danmicholoparser.preprocessor import preprocessToXml

def condition_for_soup(text):
    """
    While BeautifulSoup and its parsers are robust, (unknown) tags with
    unquoted arguments seems to be an issue.

    Let's first define a function to make things clearer:
    >>> def f(str):
    >>>     out = ''
    >>>     for tag in BeautifulSoup(str, 'lxml').findAll('body')[0].contents]):
    >>>         out.append(unicode(tag))
    >>>     return ''.join(out)

    Now, here is an unexpected result: the ref-tag is not read as closed and
    continue to eat the remaining text!
    >>> f('<ref name=XYZ/>Mer tekst her')
    <<< u'<ref name="XYZ/">Mer tekst her</ref>'

    Add a space before / and we get the expected result:
    >>> f('<ref name=XYZ />Mer tekst her')
    <<< u'<ref name="XYZ"></ref>Mer tekst her'

    Therefore we should condition the text before sending it to BS
    """
    text = re.sub(r'<ref ([^>]+)=\s?([^"\s]+)/>', r'<ref \1=\2 />', text)

    # strip whitespace at beginning of lines, as it makes finding tables harder
    text = re.sub(r'\n[\s]+', r'\n', text)

    return text


class MainText(object):
    """
    Class to extract the main text (excluding template, tables, etc.)
    from wikimarkup
    """

    def __init__(self, text):
        self.text = text
        self.errors = []
        pass

    def line_debug(self, logger, lineno, indent, tag, clip):
        logger.debug('%5d:%-10s%s',
                     lineno,
                     ''.join([' ' for s in range(indent - 1)]) + tag,
                     clip.replace('\n', '\\n'))

    @property
    def maintext(self):
        self.parse_errors = []

        xml = preprocessToXml(self.text)
        xml = xml.replace('&lt;', '<').replace('&gt;', '>')
        #print xml.encode('utf-8')

        root = fromstring(condition_for_soup(xml))

        out = u''
        if root.text:
            out += root.text
        for child in root.iterchildren():
            if child.tail:
                out += child.tail

        # Strip tables
        buf = []
        depth = 0
        cpos = 0
        while True:
            openpos = out.find('{|', cpos)
            closepos = out.find('|}', cpos)
            if openpos == -1 and closepos == -1:
                break
            elif openpos == -1:
                current = {'mark': 'close', 'pos': closepos}
            elif closepos == -1:
                current = {'mark': 'open', 'pos': openpos}
            else:
                if openpos < closepos:
                    current = {'mark': 'open', 'pos': openpos}
                else:
                    current = {'mark': 'close', 'pos': closepos}

            if current['mark'] == 'open':
                if depth == 0:
                    buf.append(out[cpos:current['pos']])
                cpos = current['pos'] + 2
                depth += 1
            else:
                cpos = current['pos'] + 2
                depth -= 1

        if depth == 0:
            buf.append(out[cpos:])
        out = ''.join(buf)

        out = re.sub(r'==[=]*', '', out)                                 # drop header markers (but keep header text)
        out = re.sub(r"''[']*", '', out)                                 # drop bold/italic markers (but keep text)
        out = re.sub(r'^#.*?$', '', out, flags=re.MULTILINE)             # drop lists altogether
        out = re.sub(r'^\*.*?$', '', out, flags=re.MULTILINE)            # drop lists altogether
        out = re.sub(r'\[\[Kategori:[^\]]+\]\]', '', out)                # drop categories
        out = re.sub(r'(?<!\[)\[(?!\[)[^ ]+ [^\]]+\]', '', out)          # drop external links
        out = re.sub(r'\[\[(?:[^:|\]]+\|)?([^:\]]+)\]\]', '\\1', out)    # wikilinks as text, '[[Artikkel 1|artikkelen]]' -> 'artikkelen'
        out = re.sub(r'\[\[(?:Fil|File|Image|Bilde):[^\]]+\|([^\]]+)\]\]', '\\1', out)  # image descriptions only
        out = re.sub(r'\[\[[A-Za-z\-]+:[^\]]+\]\]', '', out)             # drop interwikis

        out = out.strip()
        self._maintext = out
        return out

    @property
    def maintext_alt(self):

        self.parse_errors = []

        # use cached value if available
        # try:
        #     return self._maintext
        # except:
        #     pass

        xml = preprocessToXml(self.text)
        xml = xml.replace('&lt;', '<').replace('&gt;', '>')
        soup = BeautifulSoup(condition_for_soup(xml))
        root = soup.find('root')
        out = ''
        for child in root.childGenerator():
            if type(child) == NavigableString:
                out += child

        # Strip tables
        buf = []
        depth = 0
        cpos = 0
        while True:
            openpos = out.find('{|', cpos)
            closepos = out.find('|}', cpos)
            if openpos == -1 and closepos == -1:
                break
            elif openpos == -1:
                current = {'mark': 'close', 'pos': closepos}
            elif closepos == -1:
                current = {'mark': 'open', 'pos': openpos}
            else:
                if openpos < closepos:
                    current = {'mark': 'open', 'pos': openpos}
                else:
                    current = {'mark': 'close', 'pos': closepos}

            if current['mark'] == 'open':
                if depth == 0:
                    buf.append(out[cpos:current['pos']])
                cpos = current['pos'] + 2
                depth += 1
            else:
                cpos = current['pos'] + 2
                depth -= 1

        if depth == 0:
            buf.append(out[cpos:])
        out = ''.join(buf)

        out = re.sub(r'==[=]*', '', out)                                 # drop header markers (but keep header text)
        out = re.sub(r"''[']*", '', out)                                 # drop bold/italic markers (but keep text)
        out = re.sub(r'^#.*?$', '', out, flags=re.MULTILINE)             # drop lists altogether
        out = re.sub(r'^\*.*?$', '', out, flags=re.MULTILINE)            # drop lists altogether
        out = re.sub(r'\[\[Kategori:[^\]]+\]\]', '', out)                # drop categories
        out = re.sub(r'(?<!\[)\[(?!\[)[^ ]+ [^\]]+\]', '', out)          # drop external links
        out = re.sub(r'\[\[(?:[^:|\]]+\|)?([^:\]]+)\]\]', '\\1', out)    # wikilinks as text, '[[Artikkel 1|artikkelen]]' -> 'artikkelen'
        out = re.sub(r'\[\[(?:Fil|File|Image|Bilde):[^\]]+\|([^\]]+)\]\]', '\\1', out)  # image descriptions only
        out = re.sub(r'\[\[[A-Za-z\-]+:[^\]]+\]\]', '', out)             # drop interwikis

        out = out.strip()
        self._maintext = out
        return out

    @property
    def maintext_old(self):

        logger = logging.getLogger('DanmicholoParser.maintext')
        self.parse_errors = []

        # use cached value if available
        # try:
        #     return self._maintext
        # except:
        #     pass

        out = ''

        # BeautifulSoup (BS) will cleanup the html to make it more readable,
        # e.g. turning <br> into <br/>, closing unclosed tags (not necessarily
        # at the "right" place though) and so on
        soup = BeautifulSoup(condition_for_soup(self.text), 'lxml')
        bd = soup.findAll('body')
        if len(bd) == 0:
            return ''
        souped = ''.join([unicode(q) for q in bd[0].contents])

        # BS introduces paragraphs, so let's remove them
        souped = re.sub(r'<(?:/)?p>', '', souped)

        # if logger.isEnabledFor(logging.DEBUG):
        #     print 'Writing soup.dump'
        #     f = open('soup.dump', 'w')
        #     f.write(souped.encode('utf-8'))
        #     f.close()

        buf = '00'       # keep track of last two characters
        ptree = ['top']  # simple parse tree
        closing = ''     # just for debugging

        for i, c in enumerate(souped):
            try:

                if (buf[1] == '\n' or buf[1] == '0') and buf[0] == '{' and c == '|':
                    # we entered a table
                    ptree.append('table')
                    self.line_debug(logger, i, len(ptree), '{|',
                                    souped[i-1:i+10])

                elif buf[1] == '\n' and buf[0] == '|' and c == '}':
                    # we may have left a table (but we may also have met |}}
                    # at the end of a template)
                    if 'table' in ptree:
                        self.line_debug(logger, i, len(ptree), '|}',
                                        souped[i-10:i+1])
                        closing = 'table'
                        while ptree.pop() != 'table':
                            pass

                elif c == '}':
                    if buf[0] == '}':
                        # we left a template
                        if ptree[-1] == 'template':
                            self.line_debug(logger, i, len(ptree), '}}',
                                            souped[i-10:i+1])
                            ptree.pop()
                        else:
                            self.line_debug(logger, i, len(ptree),
                                            'Extra set of }}s!',
                                            souped[i-10:i+1])
                            logger.warn('Found extra set of }}s!%s',
                                        'Parse tree is: ' + ','.join(ptree))
                            self.parse_errors.append('Found extra set of }}s: "'
                                                     + souped[i-10:i+10] + '"')

                        # clear buffer to avoid }}} triggering }} twice
                        buf = '00'
                        continue

                elif c == '{':
                    if buf[0] == '{':
                        # we entered a template
                        ptree.append('template')
                        self.line_debug(logger, i, len(ptree), '{{', souped[i-1:i+10])

                        buf = '00'  # clear buffer to avoid {{{ triggering {{ twice
                        continue

                elif c == '>':
                    if buf[0] == '/':
                        # start tag is also end tag (like <br/>)
                        self.line_debug(logger, i, len(ptree), '/>', souped[i-3:i+1])
                        closing = 'starttag'
                        while ptree.pop() != 'starttag':
                            pass

                    elif ptree[-1] == 'starttag':
                        # we left a starttag
                        ptree.pop()
                        ptree.append('intag')
                        self.line_debug(logger, i, len(ptree), '>', souped[i-10:i+1])

                    else:
                        # we left an endtag
                        self.line_debug(logger, i, len(ptree), '</...>', souped[i-10:i+1])
                        closing = 'endtag/comment'
                        while ptree.pop() not in ('endtag', 'comment'):
                            pass

                elif buf[0] == '<':
                    if c == '!':
                        # we entered a comment
                        ptree.append('comment')
                        self.line_debug(logger, i, len(ptree), '<!', souped[i-1:i+10])
                    elif c == '/':
                        # we entered an end tag
                        if 'intag' in ptree:
                            closing = 'intag'
                            while ptree.pop() != 'intag':
                                pass
                        else:
                            logger.warn('%5d: Found end tag without matching start tag: %s', i, souped[i - 10:i + 10].replace('\n', '\\n'))
                            self.parse_errors.append('Extra (non-matching) end-tag encountered: "' + souped[i - 10:i + 10] + '".'
                                                     + 'This may have been inserted to compensate for a missing end-tag.')

                        ptree.append('endtag')

                    else:
                        # we entered a start tag
                        ptree.append('starttag')
                        self.line_debug(logger, i, len(ptree), '<', souped[i-1:i+10])

                elif c == '<':
                    pass

                elif len(ptree) == 1:
                    out += c

                buf = c + buf[0]

            except IndexError:
                # Last stance... most "normal" errors should just be added to self.parse_errors
                logger.error('Syntax error: Found end of %s near %d, but no start!', closing, i)
                raise DanmicholoParseError('Syntax error: Found end of %s near %d, but no start!' % (closing, i))

        if len(ptree) != 1:
            logger.error('Syntax error: %s was not closed!', ptree[-1])
            raise DanmicholoParseError('Syntax error: %s was not closed!' % ptree[-1])

        out = re.sub(r'==[=]*', '', out)                                 # drop header markers (but keep header text)
        out = re.sub(r"''[']*", '', out)                                 # drop bold/italic markers (but keep text)
        out = re.sub(r'^#.*?$', '', out, flags=re.MULTILINE)             # drop lists altogether
        out = re.sub(r'^\*.*?$', '', out, flags=re.MULTILINE)            # drop lists altogether
        out = re.sub(r'\[\[Kategori:[^\]]+\]\]', '', out)                # drop categories
        out = re.sub(r'(?<!\[)\[(?!\[)[^ ]+ [^\]]+\]', '', out)          # drop external links
        out = re.sub(r'\[\[(?:[^:|\]]+\|)?([^:\]]+)\]\]', '\\1', out)    # wikilinks as text, '[[Artikkel 1|artikkelen]]' -> 'artikkelen'
        out = re.sub(r'\[\[(?:Fil|File|Image|Bilde):[^\]]+\|([^\]]+)\]\]', '\\1', out)  # image descriptions only
        out = re.sub(r'\[\[[A-Za-z\-]+:[^\]]+\]\]', '', out)             # drop interwikis

        self._maintext = out.strip()

        return out
