# encoding=utf-8

from __future__ import unicode_literals
import re
import sys, codecs
from copy import copy
from odict import odict # ordered dict (replace by OrderedDict on Python 3)
from danmicholoparser import DanmicholoParseError

import logging
logger = logging.getLogger(__name__)

def get_whitespace(txt):

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
            right = rl.group(0)
    return (left, right)

class DpTemplate(object):
    """ A single template instance """

    def __init__(self, obj):
        self.name="?"
        self.parameters = odict()
        self._paramnames = odict()
        self._paramspace = odict()

        self.begin = obj['begin']
        self.end = obj['end']
        self.name = obj['name'].strip() # not lower-cased
        self._name_ws = get_whitespace(obj['name']) # preserve surrounding whitespace
        self._txt = obj['txt']
            
        # Filter out empty parameters:
        #splits = filter(lambda x: x != '', obj['splits'])
        splits = obj['splits']

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
                self._paramspace[pno] = get_whitespace(s[0])
                pno += 1
            elif len(s) == 2:
                # Named parameter:
                #wspacee = re.search('([\s])+$',s[1]).group(0)
                sname = s[0].strip()
                if sname in self.parameters:
                    if self.parameters[sname] == s[1].strip():
                        logger.warn('The same parameter "%s" was passed twice to a template "%s", but with the same value, so we can just chop off one')
                    else:
                        raise DanmicholoParseError('Ambigious: The same parameter "%s" was passed twice to a template "%s":\n\n%s' % (sname, self.name, self._txt))
                else:
                    self.parameters[sname] = s[1].strip()
                    self._paramnames[sname] = s[0]  # save the original, unstripped form
                    self._paramspace[sname] = get_whitespace(s[1])
            else:
                raise DanmicholoParseError("Wrong len %d in %s " % (len(s), s))
    
    def has_param(self, name):
        """ Returns true if the parameter is defined and non-empty """
        return name in self.parameters.keys() and self.parameters[name] != ''

    def modified(self):
        return self._txt != self.getwikitext()

    def original_length(self):
        return self.end - self.begin

    def current_length(self):
        return len(self.getwikitext())

    def getwikitext(self):
        tmp = '{{' + self._name_ws[0] + self.name + self._name_ws[1]

        prevsp = ['', ' ', ' ', '']

        for p in self.parameters:

            if p not in self._paramnames:
                # this is a new parameter, added during runtime
                # we *try* to use the same whitespace convention as the previous parameter (indentation is not currently inherited)
                tmp += '|' + prevsp[0] + p + prevsp[1] + '=' + prevsp[2] + self.parameters[p] + prevsp[3] 

            else:

                # The parameter key 'p' have surrounding whitespace stripped off for easy lookup, 
                # but the original form is preserved in self._paramnames[p]
                pnam = self._paramnames[p]  

                # we've also saved the whitespace surround the parameter value:
                sp = self._paramspace[p]

                if pnam == '':
                    # anonymous parameter:
                    tmp += '|' + sp[0] + self.parameters[p] + sp[1]
                    prevsp = [sp[0], ' ', ' ', sp[1]]
                else:
                    # named parameter:
                    tmp += '|' + pnam+ '=' + sp[0] + self.parameters[p] + sp[1]
                    w = get_whitespace(pnam)
                    prevsp = [w[0], w[1], sp[0], sp[1]]

        tmp += '}}'
        return tmp
    
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s = "<%s>" % (self.name.strip())
        for k in self.parameters.keys():
            s += "\n  %s = %s" % (k, self.parameters[k])
        return s


class TemplateEditor(object):
    """ Class to parse and edit templates in wikimarkup """

    def __init__(self, text):
        self.text = text
        self.errors = []

    def get_templates(self):
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
    @property
    def templates(self):
        return self.get_templates()

    def clean_p(self,p):
        p = p.split('=',1)
        return [s.strip() for s in p]

    def scan_for_templates(self, text, level = 0, start = 0):
        """ Recursive template scanner """
        logger = logging.getLogger('TemplateEditor.scan_for_templates')
        
        if level > 20:
            logger.error('Too many recusions encountered!')
            raise DanmicholoParseError('Too many recusions encountered!')

        spaces = ''.join([' ' for i in range(level)])

        logger.debug('%s> scan (offset = %d, length = %d)', spaces, start, len(text))

        # We should keep track of all brackets, so we don't split inside a bracketed part:
        brackets = { 'round' : 0, 'square': 0, 'curly': 0, 'angle': 0 }
        brackets_before = { 'square': 0, 'angle': 0 }
        templates = []
        intemplate = -1
        tmp = ''
        p = start - 1
        buf = '    '
        incomment = False
        for c in text:
            p += 1
            storeprev = True
            
            # should check this first
            if buf == '<!--':
                incomment = True
            elif buf[1:4] == '-->':
                incomment = False
                
            if not incomment:
                if c == ')': brackets['round'] -= 1
                elif c == ']': brackets['square'] -= 1
                elif buf[-1] == '}' and c == '}': 
                    logger.debug('[%s] }}', p)
                    brackets['curly'] -= 2
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
                    #logger.debug(spaces+"  "+c,"end, Name="+templates[intemplate]['name'],templates[intemplate]['begin'],templates[intemplate]['end']

                    # Scan all splits for sub-templates:
                    offset = start + templates[intemplate]['begin'] + 2 + len(navn) + 1
                    #print offset
                    for s in templates[intemplate]['splits']:
                        #print s
                        templates = templates + self.scan_for_templates(s, level = level + 1, start = offset)
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
                elif buf[-1] == '{' and c == '{': 
                    logger.debug('[%s] {{', p)
                    brackets['curly'] += 2
                    storeprev = False
                
                elif c == '<': brackets['angle'] += 1

            if storeprev:
                buf = buf[1:4] + c
            else:
                buf = buf[1:4] + ' '

        if brackets['curly'] != 0:
            raise DanmicholoParseError('Unbalanced curly brackets encountered (%d)!' % brackets['curly'])
        
        logger.debug('%s  return %d templates', spaces, len(templates))
        return templates


    def reparse(self):
        del self._templates
        self.text = get_wikitext(self)

    def modified(self):
        for key in self.templates:
            for t in self.templates[key]:
                if t.modified():
                    return True
        return False

    def get_wikitext(self):
        mod = 0
        txt = copy(self.text)
        for key in self.templates:
            for t in self.templates[key]:
                if t.modified():
                    #print "MODIFIED:",t.parameters['id']
                    #print t._txt
                    #print '---------------------------'
                    #print t.getwikitext()
                    
                    if mod > 0:
                        raise StandardError("Uh oh, can only handle one modification a time")
                    txt = txt[:t.begin] + t.getwikitext() + txt[t.end:]
                    mod += 1
                #print t.begin
        return txt
