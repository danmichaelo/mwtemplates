# encoding=utf-8

from __future__ import unicode_literals
from templateeditor import TemplateEditor
from maintext import MainText

import logging
logger = logging.getLogger(__name__)

class DanmicholoParseError(Exception):

    def __init__(self, msg):
        self.msg = msg
        self.parse_errors = []

class DanmicholoParser(TemplateEditor, MainText):

    def __init__(self, text):
        self.text = text
        self.errors = []
    

    @property
    def tags(self):
        """
        A simple and unsophisticated HTML parser, does not even handle things like tags inside tags, 
        but those should be avoided in wikitext I think. 

        Returns a dictionary of tag names, with each dictionary item containing a list of the occurances of that tag,
        so you can do things like this:

        >>> nrefs = len([r for r in dp.tags['ref'] if 'content' in r])

        >>> for r in tags['ref']:
        >>>    if 'name' in r:
        >>>        print r['name']

        """

        # use cached value if available
        try:
            return self._tags
        except:
            pass

        tags = {}
        state = ''
        starttag = ''
        tagcontent = ''
        for i,c in enumerate(self.text):
            if state == 'starttag' and c == '>':
                state = 'intag'
            elif state == 'comment' and c == '>':
                state = ''
            elif state == 'endtag' and c == '>':
                state = ''
                starttag = starttag.strip().split()
                try:
                    tagname = starttag[0]
                except:
                    #if self.raise_errors:
                    #raise DanmicholoParseError("Blank/invalid html tag encountered near %d" % i)
                    self.errors.append("Blank/invalid html tag encountered near %d" % i)
                    if len(self.errors) > 10:
                        self.errors.append("Too many errors. I'm giving up")
                        break
                    continue
                tag = { }
                for a in starttag[1:]:
                    aa = [q.strip(' "\'') for q in a.split('=')]
                    if len(aa)==2:
                        tag[aa[0]] = aa[1]
                if len(tagcontent) > 0:
                    tag['content'] = tagcontent.strip()
                if not tagname in tags:
                    tags[tagname] = []
                tags[tagname].append(tag)

            elif state == 'intag' and c == '<':
                state = 'endtag'
            elif state == '' and c == '<':
                state = 'starttag'
                starttag = ''
                tagcontent = ''
            elif state == 'starttag' and c == '/':
                state = 'endtag'
            elif state == 'starttag' and c == '!':
                state = 'comment'
            elif state == 'starttag':
                starttag += c
            elif state == 'intag':
                tagcontent += c

        self._tags = tags
        
        return tags



