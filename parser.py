#!/usr/bin/env python
# encoding=utf-8

from __future__ import unicode_literals
import re
import sys, codecs
from copy import copy
from odict import odict # ordered dict (replace by OrderedDict on Python 3)
from bs4 import BeautifulSoup

def condition_for_soup(text):
    """
    While BeautifulSoup and its parsers are robust, (unknown) tags with unquoted arguments seems to be an issue.

    Let's first define a function to make things clearer:
    >>> def f(str):
    >>>     return ''.join([unicode(tag) for tag in BeautifulSoup(str, 'lxml').findAll('body')[0].contents])

    Now, here is an unexpected result: the ref-tag is not read as closed and continue to eat the remaining text!
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


class DanmicholoParseError(Exception):

    def __init__(self, msg):
        self.msg = msg
        self.parse_errors = []


class DpTemplate(object):

    def getwhitespace(self, txt):

        left = ''
        # find whitespace to the left of the parameter
        rl = re.search('^([\s])+', txt)
        if rl:
            left = rl.group(0)
        right = ''

        rall = re.search('^([\s])+$', txt)
        # unless the entire parameter is whitespace 
        if not rall:
            # find whitespace to the right of the parameter
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
                # Anonymous parameter:
                #wspaceb = re.search('^([\s])+',s[0])
                #wspacee = re.search('([\s])+$',s[0])
                self.parameters[pno] = s[0].strip()
                self._paramnames[pno] = ''
                self._paramspace[pno] = self.getwhitespace(s[0])
                pno += 1
            elif len(s) == 2:
                # Named parameter:
                #wspacee = re.search('([\s])+$',s[1]).group(0)
                self.parameters[s[0].strip()] = s[1].strip()
                self._paramnames[s[0].strip()] = s[0]  # save the original, unstripped form
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

            if p not in self._paramnames:
                # this is a new parameter, added during runtime
                tmp += '|' + p + '=' + self.parameters[p]

            else:

                # The parameter key 'p' have surrounding whitespace stripped off for easy lookup, 
                # but the original form is preserved in self._paramnames[p]
                pnam = self._paramnames[p]  

                # we've also saved the whitespace surround the parameter value:
                sp = self._paramspace[p]

                if pnam == '':
                    # anonymous parameter:
                    tmp += '|' + sp[0] + self.parameters[p] + sp[1]
                else:
                    # named parameter:
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
            print "%s> scan (offset = %d, length = %d, txt = \"%s\")" % (spaces, start, len(text), text)
            #print spaces +"  "+text

        # We should keep track of all brackets, so we don't split inside a bracketed part:
        brackets = { 'round' : 0, 'square': 0, 'curly': 0, 'angle': 0 }
        brackets_before = { 'square': 0, 'angle': 0 }
        templates = []
        intemplate = -1
        tmp = ''
        p = start - 1
        prev = ''
        for c in text:
            p += 1
            storeprev = True
            if c == ')': brackets['round'] -= 1
            elif c == ']': brackets['square'] -= 1
            elif prev == '}' and c == '}': 
                if debug:
                    print p,'}}'
                brackets['curly'] -= 2
                prev = ''
                storeprev = False
            elif c == '>': brackets['angle'] -= 1
            
            if intemplate != -1 and brackets['curly'] < 2:
                templates[intemplate]['end'] = p + 1
                templates[intemplate]['splits'].append(tmp[:-1]) # skip ending }
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
                brackets_before = brackets.copy()
                tmp = ''

            if intemplate != -1 and c == '|' and brackets['square'] == brackets_before['square'] and brackets['angle'] == brackets_before['angle'] and brackets['curly'] == 2:
                templates[intemplate]['splits'].append(tmp)
                tmp = ''
            else:
                tmp += c

            if c == '(':   brackets['round'] += 1
            elif c == '[': brackets['square'] += 1
            elif prev == '{' and c == '{': 
                if debug:
                    print p,'{{'
                brackets['curly'] += 2
                storeprev = False
                prev = ''
                
            elif c == '<': brackets['angle'] += 1

            if storeprev:
                prev = c

        if brackets['curly'] != 0:
            raise DanmicholoParseError('Unbalanced curly brackets encountered (%d)!' % brackets['curly'])
        
        if debug:
            print "%s  return %d templates" % (spaces,len(templates))
        return templates

    @property
    def maintext(self):

        debug = False
        self.parse_errors = []

        # use cached value if available
        try:
            return self._maintext
        except:
            pass

        out = ''

        # BeautifulSoup (BS) will cleanup the html to make it more readable, e.g. turning <br> into <br/>,
        # closing unclosed tags (not necessarily at the "right" place though) and so on
        soup = BeautifulSoup(condition_for_soup(self.text), 'lxml')
        bd = soup.findAll('body')
        if len(bd) == 0:
            return ''
        souped = ''.join([unicode(q) for q in bd[0].contents])

        # BS introduces paragraphs, so let's remove them
        souped = re.sub(r'<(?:/)?p>','', souped) 

        if debug:
            f = open('soup.dump','w')
            f.write(souped.encode('utf-8'))
            f.close()

        buf = '00'       # keep track of last two characters
        ptree = ['top']  # simple parse tree
        closing = ''     # just for debugging

        for i,c in enumerate(souped):
            try:

                if (buf[1] == '\n' or buf[1] == '0') and buf[0] == '{' and c == '|':
                    # we entered a table
                    ptree.append('table')
                    if debug:
                        print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '{|') + souped[i-1:i+10].replace('\n','\\n')

                elif buf[1] == '\n' and buf[0] == '|' and c == '}':
                    # we may have left a table (but we may also have met |}} at the end of a template)
                    if 'table' in ptree:
                        if debug:
                            print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '|}') + souped[i-10:i+1].replace('\n','\\n')
                        closing = 'table'
                        while ptree.pop() != 'table':
                            pass
                
                elif c == '}': 
                    if buf[0] == '}':
                        # we left a template
                        if ptree[-1] == 'template':
                            if debug:
                                print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '}}') + souped[i-10:i+1].replace('\n','\\n')
                            ptree.pop()
                        else:
                            if debug:
                                print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + 'Extra set of }}s!') \
                                        + souped[i-10:i+1].replace('\n','\\n') + 'Parse tree: ' + ','.join(ptree)

                                #print "Found extra set of }}s"
                            self.parse_errors.append('Found extra set of }}s: "' + souped[i-10:i+10] + '"')
                            
                        buf = '00' # clear buffer to avoid }}} triggering }} twice
                        continue

                elif c == '{': 
                    if buf[0] == '{':
                        # we entered a template
                        ptree.append('template')
                        if debug:
                            print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '{{') + souped[i-1:i+10].replace('\n','\\n')
                        
                        buf = '00' # clear buffer to avoid {{{ triggering {{ twice
                        continue

                elif c == '>': 
                    if buf[0] == '/':
                        # start tag is also end tag (like <br/>)
                        if debug:
                            print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '/>') + souped[i-3:i+1].replace('\n','\\n')
                        closing = 'starttag'
                        while ptree.pop() != 'starttag':
                            pass

                    elif ptree[-1] == 'starttag':
                        # we left a starttag
                        ptree.pop()
                        ptree.append('intag')
                        if debug:
                            print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '>') + souped[i-10:i+1].replace('\n','\\n')

                    else:
                        # we left an endtag
                        if debug:
                            print '%5d:'%i + '%-10s' % (''.join([' ' for s in range(len(ptree)-1)]) + '</...>') + souped[i-10:i+1].replace('\n','\\n')
                        closing = 'endtag/comment'
                        while ptree.pop() not in ('endtag','comment'):
                            pass


                elif buf[0] == '<':
                    if c == '!':
                        # we entered a comment
                        ptree.append('comment')
                        if debug:
                            print '%5d:'%i + '%-10s' %(''.join([' ' for s in range(len(ptree)-1)]) + '<!') + souped[i-1:i+10].replace('\n','\\n')
                    elif c == '/':
                        # we entered an end tag
                        if 'intag' in ptree:
                            closing = 'intag'
                            while ptree.pop() != 'intag':
                                pass
                        else:
                            if debug:
                                print 'WARNING: %5d:'%i + 'Found end tag without matching start tag' + souped[i-1:i+10].replace('\n','\\n')
                                print "Found end tag without a matching start tag!" + souped[i-1:i+10].replace('\n','\\n')
                            self.parse_errors.append('Extra (non-matching) end-tag encountered: "' + souped[i-10:i+10] + '". This may have been inserted to compensate for a missing end-tag.')
                        
                        ptree.append('endtag')

                    else:
                        # we entered a start tag
                        ptree.append('starttag')
                        if debug:
                            print '%5d:'%i  + '%-10s' %(''.join([' ' for s in range(len(ptree)-1)]) + '<') + souped[i-1:i+10].replace('\n','\\n')

                elif c == '<':
                    pass

                elif len(ptree) == 1:
                    out += c

                buf = c + buf[0]

            except IndexError as e:
                # Last stance... most "normal" errors should just be added to self.parse_errors
                if debug:
                    print 'ERROR: Syntax error: Found end of %s near %d, but no start!'%(closing,i)
                raise DanmicholoParseError('Syntax error: Found end of %s near %d, but no start!'%(closing,i))
        
        if len(ptree) != 1:
            raise DanmicholoParseError('Syntax error: %s was not closed!'%ptree[-1])

        out = re.sub(r'==[=]*','', out)                                 # drop header markers (but keep header text)
        out = re.sub(r"''[']*",'', out)                                 # drop bold/italic markers (but keep text)
        out = re.sub(r'^#.*?$','', out, flags = re.MULTILINE)           # drop lists altogether
        out = re.sub(r'^\*.*?$','', out, flags = re.MULTILINE)          # drop lists altogether
        out = re.sub(r'\[\[Kategori:[^\]]+\]\]','', out)                # drop categories
        out = re.sub(r'(?<!\[)\[(?!\[)[^ ]+ [^\]]+\]','', out)          # drop external links
        out = re.sub(r'\[\[(?:[^:|\]]+\|)?([^:\]]+)\]\]', '\\1', out)   # wikilinks as text, '[[Artikkel 1|artikkelen]]' -> 'artikkelen'
        out = re.sub(r'\[\[(?:Fil|File|Image|Bilde):[^\]]+\|([^\]]+)\]\]', '\\1', out)  # image descriptions only
        out = re.sub(r'\[\[[A-Za-z\-]+:[^\]]+\]\]','', out)             # drop interwikis
        
        self._maintext = out.strip()

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
        
        txt = re.sub('<nowiki>.+?</nowiki>', '', self.text)
        templates = self.scan_for_templates(txt)
        
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
                    txt = txt[:t.begin] + t.getwikitext() + txt[t.end:]
                    mod += 1
                #print t.begin
        return txt

