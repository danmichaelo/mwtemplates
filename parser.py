#!/usr/bin/env python
# encoding=utf-8

from __future__ import unicode_literals
import re
import sys, codecs
from copy import copy
from odict import odict # ordered dict (replace by OrderedDict on Python 3)
from bs4 import BeautifulSoup


class DanmicholoParseError(Exception):

    def __init__(self, msg):
        self.msg = msg


class DpTemplate(object):

    def getwhitespace(self, txt):
        left = ''
        rl = re.search('^([\s])+', txt)
        if rl:
            left = rl.group(0)
        right = ''
        rl = re.search('([\s])+$', txt)
        if rl:
            right= rl.group(0)
        return (left, right)

    def __init__(self, obj):
        self.name="?"
        self.parameters = odict()
        self._paramnames = odict()
        self._paramspace = odict()

        self.begin = obj['begin']
        self.end = obj['end']
        self.name = obj['name'] # preserve original form
        self._txt = obj['txt']
            
        # Filter out empty parameters:
        splits = filter(lambda x: x != '', obj['splits'])

        # Index for anonymous parameters starts at 1 for consistency with WP:
        pno = 1

        for s in splits:
            s = s.split('=',1)
            #[q.strip() for q in s.split('=',1)]
            if len(s) == 1:
                #wspaceb = re.search('^([\s])+',s[0])
                #wspacee = re.search('([\s])+$',s[0])
                self.parameters[pno] = s[0].strip()
                self._paramnames[pno] = ''
                self._paramspace[pno] = self.getwhitespace(s[0])
                pno += 1
            elif len(s) == 2:
                #wspacee = re.search('([\s])+$',s[1]).group(0)
                self.parameters[s[0].strip()] = s[1].strip()
                self._paramnames[s[0].strip()] = s[0]  # original, unstripped
                self._paramspace[s[0].strip()] = self.getwhitespace(s[1])
            else:
                raise DanmicholoParseError("Wrong len %d in %s " % (len(s), s))

    def modified(self):
        return self._txt != self.getwikitext()

    def original_length(self):
        return self.end - self.begin

    def current_length(self):
        return len(self.getwikitext())

    def getwikitext(self):
        tmp = '{{'+self.name
        for p in self.parameters:
            pnam = self._paramnames[p]
            sp = self._paramspace[p] 
            if pnam == '':
                tmp += '|' + sp[0] + self.parameters[p] + sp[1]
            else:
                tmp += '|' + pnam+ '=' + sp[0] + self.parameters[p] + sp[1]
        tmp += '}}'
        return tmp
    
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s = "<%s>" % (self.name.strip())
        for k in self.parameters.keys():
            s += "\n  %s = %s" % (k, self.parameters[k])
        return s




class DanmicholoParser(object):

    def clean_p(self,p):
        p = p.split('=',1)
        return [s.strip() for s in p]

    def __init__(self, text, debug = False):
        #self.parse(text, debug = debug)
        self.text = text
        self.errors = []
        pass


    def scan_for_templates(self, text, level = 0, debug = False, start = 0):
        """Recursive template scanner"""
        
        if level > 20:
            raise DanmicholoParseError("Too many recusions encountered!")

        spaces = ''.join([' ' for i in range(level)])
        if debug:
            print "%s> scan (offset = %d, length = %d)" % (spaces, start, len(text))
            #print spaces +"  "+text

        # We should keep track of all brackets, so we don't split inside a bracketed part:
        brackets = { 'round' : 0, 'square': 0, 'curly': 0, 'angle': 0 }
        templates = []
        intemplate = -1
        tmp = ''
        p = start - 1
        for c in text:
            p += 1
            if c == ')': brackets['round'] -= 1
            elif c == ']': brackets['square'] -= 1
            elif c == '}': brackets['curly'] -= 1
            elif c == '>': brackets['angle'] -= 1
            
            if intemplate != -1 and brackets['curly'] < 2:
                templates[intemplate]['end'] = p + 2
                templates[intemplate]['splits'].append(tmp)
                #templates[intemplate]['splits'] = map(self.clean_p, templates[intemplate]['splits'])
                #print templates[-1]['splits']
                navn = templates[intemplate]['splits'].pop(0).strip('{')
                templates[intemplate]['name'] = navn
                templates[intemplate]['txt'] = text[templates[intemplate]['begin']-start:templates[intemplate]['end']-start]
                #if debug:
                #    print spaces+"  "+c,"end, Name="+templates[intemplate]['name'],templates[intemplate]['begin'],templates[intemplate]['end']

                # Scan all splits for sub-templates:
                offset = start + templates[intemplate]['begin'] + 2 + len(navn) + 1
                #print offset
                for s in templates[intemplate]['splits']:
                    #print s
                    templates = templates + self.scan_for_templates(s, level = level + 1, debug = debug, start = offset)
                    offset += len(s) + 1
                    #offset += 1 # for the pipe

                intemplate = -1
            elif intemplate == -1 and brackets['curly'] >= 2:
                #if debug:
                #    print spaces +"  Template start at ",c
                templates.append({'begin':p-2, 'end':-1, 'splits':[]})
                intemplate = len(templates)-1
                tmp = ''

            if intemplate != -1 and c == '|' and brackets['round'] == brackets['square'] == brackets['angle'] == 0 and brackets['curly'] == 2:
                templates[intemplate]['splits'].append(tmp)
                tmp = ''
            else:
                tmp += c

            if c == '(':   brackets['round'] += 1
            elif c == '[': brackets['square'] += 1
            elif c == '{': brackets['curly'] += 1
            elif c == '<': brackets['angle'] += 1

        if brackets['curly'] != 0:
            raise DanmicholoParseError('Unbalanced curly brackets encountered!')
        
        if debug:
            print "%s  return %d templates" % (spaces,len(templates))
        return templates

    @property
    def maintext(self):

        # use cached value if available
        try:
            return self._maintext
        except:
            pass

        # We should keep track of all brackets, so we don't split inside a bracketed part:
        brackets = { 'round' : 0, 'square': 0, 'curly': 0, 'angle': 0 }
        intag = False
        out = ''

        soup = BeautifulSoup(self.text)
        souped = ''.join([unicode(q) for q in soup.findAll('p')[0].contents])
        for c in souped:
            
            #elif c == ']': brackets['square'] -= 1
            #elif c == '}': brackets['curly'] -= 1
            #elif c == '>': brackets['angle'] -= 1
            #elif c == '(':   brackets['round'] += 1
            #elif c == '[': brackets['square'] += 1

            if c == '}': 
                brackets['curly'] -= 1
                if brackets['angle'] > 0:
                    brackets['angle'] = 0
                    intag = False
            elif c == '{': 
                brackets['curly'] += 1
            elif c == '>': 
                brackets['angle'] -= 1
            elif c == '<': 
                brackets['angle'] += 1
                intag = True
            elif brackets['angle'] == 1 and c == '/':
                intag = False
            elif brackets['curly'] == 0 and brackets['angle'] == 0 and intag == False:
                out += c

        #print len(out), brackets['curly'], brackets['angle']
        out = re.sub(r'==[=]*','', out)
        out = re.sub(r"''[']*",'', out)
        out = re.sub(r'^#.*?$','', out, flags = re.MULTILINE)            # drop lists
        out = re.sub(r'^\*.*?$','', out, flags = re.MULTILINE)           # drop lists
        out = re.sub(r'\[\[Kategori:[^\]]+\]\]','', out)         # drop categories
        out = re.sub(r'\[\[[a-z]{2,3}:[^\]]+\]\]','', out)       # drop interwikis
        out = re.sub(r'(?<!\[)\[(?!\[)[^ ]+ [^\]]+\]','', out)   # drop external links
        out = re.sub(r'\[\[(?:[^|\]]+\|)?([^\]]+)\]\]', '\\1', out)  # wikilinks as text, '[[Artikkel 1|artikkelen]]' -> 'artikkelen'
        
        self._maintext = out.strip()
        
        #if intag:
        #    raise DanmicholoParseError('Non-closed html tag encountered!')
        #if brackets['curly'] != 0:
        #    raise DanmicholoParseError('Unbalanced curly brackets encountered!')

        return out

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


    @property
    def templates(self):
        try:
            return self._templates
        except:
            pass
        
        templates = self.scan_for_templates(self.text)
        
        self._templates = odict()

        for t in templates:
            
            dt = DpTemplate(t)
            #print dt

            k = dt.name.strip().lower()
            if k in self._templates:
                self._templates[k].append(dt)
            else:
                self._templates[k] = [dt]

        return self._templates

    def reparse(self):
        del self._templates
        self.text = unicode(self)
        #self.parse(unicode(self))

    #def parse(self, text, debug = False):

            

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        mod = 0
        txt = copy(self.text)
        for key in self.templates:
            for t in self.templates[key]:
                if t.modified():
                    if mod > 0:
                        raise StandardError("Uh oh, can only handle one modification a time")
                    txt = txt[:t.begin] + t.getwikitext() + txt[t.end+1:]
                    mod += 1
                #print t.begin
        return txt

