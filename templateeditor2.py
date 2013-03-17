#encoding=utf-8
from __future__ import unicode_literals

# <root>LLorem ipsum <template>
# <title>
#     <tplarg>
#         <title>Min lille mal</title>
#     </tplarg>
# </title>
# <part>
#     <name index="1"/>
#     <value>sorona</value>
# </part>
# <part>
#     <name>Kake</name>=<value>sake</value>
# </part>
# </template>
# </root>


# <root>LLorem ipsum
# <template>
#   <title>
#       <tplarg>
#           <title>
#               Min
#               <template>
#                   <title>lille</title>
#               </template>
#               mal
#           </title>
#       </tplarg>
#       son
#   </title>
# <part>
#     <name index="1"/>
#     <value>sorona</value>
# </part>
# <part>
#     <name>Kake</name>=<value>sake</value>
# </part>
# </template>
# </root>


import logging
import re
from lxml import etree
from StringIO import StringIO
#from odict import odict
from preprocessor import preprocessToXml
from unittest.util import safe_repr

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def most_common(lst):
    return max(set(lst), key=lst.count)


def get_whitespace(txt):

    # if the entire parameter is whitespace
    rall = re.search('^([\s])+$', txt)
    if rall:
        tmp = txt.split('\n', 1)
        if len(tmp) == 2:
            return (tmp[0], '\n' + tmp[1])
        else:
            return (tmp, '')
    left = ''
    # find whitespace to the left of the parameter
    rl = re.search('^([\s])+', txt)
    if rl:
        left = rl.group(0)
    right = ''
    # find whitespace to the right of the parameter
    rr = re.search('([\s])+$', txt)
    if rr:
        right = rr.group(0)
    return (left, right)

# try:
#     self.doc = etree.parse(StringIO(docstr), parser)
#     #self.doc = etree.parse(self.filename, parser)
#     for e in parser.error_log:
#         print "Warning: "+e.message
# except etree.XMLSyntaxError:
#     print "Failed to parse xml file: ",filename
#     for e in parser.error_log:
#         print "Warning: "+e.message
#     sys.exit(2)


def get_wikitext(node):
    tmp = ''
    if node.text is not None:
        tmp += node.text
    for child in node:
        if child.tag == 'tplarg':
            tmp += '{{{%s}}}' % get_wikitext(child)
        elif child.tag == 'template':
            tmp += '{{%s}}' % get_wikitext(child)
        elif child.tag in ['title', 'name', 'value']:
            tmp += get_wikitext(child)
        elif child.tag == 'part':
            tmp += '|' + get_wikitext(child)
        else:
            raise StandardError("Found unknown tag: %s" % etree.tostring(child))
        if child.tail is not None:
            tmp += child.tail
    return tmp


def get_arg(node):
    node.xpath('name')[0]
    node.xpath('value')[0]


class Templates(object):
    """ Dictionary-like object with first character case-insensitive """

    def __init__(self, editor, doc):
        self.editor = editor
        self.doc = doc
        #self._entries = []

    def _templates(self):
        templates = []
        for node in self.doc.findall('.//template'):
            templates.append(Template(node, self.editor))
        return templates

    # def add(self, node):
    #     self._entries.append(Template(node, self.editor))

    def __contains__(self, x):
        x = x[0].upper() + x[1:]
        for e in self._templates():
            if e.key == x:
                return True
        return False

    def __getitem__(self, x):
        x = x[0].upper() + x[1:]
        return [e for e in self._templates() if e.key == x]
        #raise KeyError

    def __repr__(self):
        return self._templates().__repr__()

    def __len__(self):
        return len(self._templates())

    def keys(self):
        return [e.key for e in self._templates()]

    def items(self):
        return {e.key: e for e in self._templates()}

    # def __contains__(self, x):
    #     return self.get_key(x) in self._entries

    # def __getitem__(self, x):
    #     return self._entries[self.get_key(x)]

    # def __setitem__(self, x, val):
    #     self._entries[self.get_key(x)] = val

    # def values():
    #     return self._entries.values()

    # def items(self):
    #     return self._entries.items()


class Parameters(object):
    """ Dictionary-like object """

    def __init__(self, template):
        self._entries = []
        self.template = template

    def __contains__(self, x):
        for e in self._entries:
            if e.key == x:
                return True
        return False

    def __getitem__(self, x):
        for e in self._entries:
            if e.key == x:
                return e
        raise KeyError

    def __setitem__(self, x, val):
        if type(val) in [unicode, str, int]:
            for entry in self._entries:
                if entry.key == x:
                    # parameter changed:
                    entry.edit(val)
                    return
            # new parameter:
            name_ws, value_ws = self.find_whitespace_pattern()
            #print '"' + whitespace[0] + '", "' + whitespace[1] + '"'
            name = name_ws[0] + x + name_ws[1]
            val = value_ws[0] + val + value_ws[1]
            parentnode = self.template.node
            node = etree.XML('<part><name>%s</name>=<value>%s</value></part>' % (name, val))
            parentnode.append(node)
            self.add(node)
        else:
            raise TypeError

    def __delitem__(self, x):
        for i, entry in enumerate(self._entries):
            if entry.key == x:
                # parameter changed:
                logger.debug('Removing parameter "%s"', entry.key)
                self.template.node.remove(entry.node)
                del self._entries[i]
                return
        raise KeyError

    def __repr__(self):
        return self._entries.__repr__()

    # def items(self):
    #     return self._entries.items()

    # def keys(self):
    #     return self._entries.keys()

    def __iter__(self):
        for e in self._entries:
            yield e

    def add(self, node):
        self._entries.append(Parameter(node))

    def find_whitespace_pattern(self):
        name_ws = []
        value_ws = []
        for entry in self._entries:
            name_ws.append(get_whitespace(entry.name))
            if entry.value.strip() != '':
                value_ws.append(get_whitespace(entry.value))
        if len(value_ws) > 2:
            value_ws = most_common(value_ws)
        else:
            value_ws = (' ', '')
        if len(name_ws) > 2:
            name_ws = most_common(name_ws)
        else:
            name_ws = (' ', '')
        return name_ws, value_ws


class Parameter(object):

    def __init__(self, node):
        self.node = node
        namenode = node.xpath('name')[0]
        self._name = get_wikitext(namenode)
        self._value = get_wikitext(node.xpath('value')[0])
        idx = namenode.get('index')
        if idx:
            self._index = int(idx)
        else:
            self._index = -1
        logger.debug('  added parameter: %s=%s', self._name.strip(), self._value.strip())

    def edit(self, val):
        logger.debug('Parameter "%s" changed: "%s" -> "%s"', self.key, self.value.strip(), val)
        whitespace = get_whitespace(self._value)
        self._value = whitespace[0] + unicode(val) + whitespace[1]
        # self.node.xpath('value')[0].text = self._value
        self.node.replace(self.node.xpath('value')[0], etree.XML('<value>' + self._value + '</value>'))

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._name

    @property
    def key(self):
        if self.index != -1:
            return self.index
        else:
            return self.name.strip()

    @property
    def value(self):
        return self._value.strip()

    def __eq__(self, x):
        #print type(x)
        if type(x) == unicode or type(x) == int:
            return self.__unicode__() == unicode(x)
        elif type(x) == str:
            return self.__str__() == x
        else:
            return False

    def __ne__(self, x):
        return not self.__eq__(x)

    def __unicode__(self):
        return self._value.strip()

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __repr__(self):
        return safe_repr(self._value.strip())


class Template(object):

    def __init__(self, node, editor):

        logger.debug('TemplateEditor got new template')

        self.node = node
        self.editor = editor
        self._name = ''
        self.parameters = Parameters(self)
        for e in node:
            if e.tag == 'title':
                self._name = get_wikitext(e)
                logger.debug('  name: %s', self.name)
            elif e.tag == 'part':
                self.parameters.add(e)

    def __repr__(self):
        return safe_repr(self.key)

    @property
    def key(self):
        tmp = self._name.strip()
        tmp = re.sub(ur'^(?:mal|template):', '', tmp, flags=re.I)
        return tmp[0].upper() + tmp[1:]

    @property
    def name(self):
        return self.key

    @name.setter
    def name(self, val):
        whitespace = get_whitespace(self._name)
        self._name = whitespace[0] + val + whitespace[1]
        self.node.xpath('title')[0].text = self._name

    def has_param(self, name):
        """ Returns True if the parameter is defined and non-empty """
        return name in self.parameters and self.parameters[name] != ''

    def get_anonymous_parameters(self):
        """ Returns True if the parameter is defined and non-empty """
        r = {}
        for x in self.parameters:
            if type(x.key) == int:
                r[x.key] = x.value
        lst = [None]
        for x in range(1, max(r.keys()) + 1):
            print x, r[x]
            lst.append(r[x])
        return lst

    def __str__(self):
        tmp = '{{%s' % self._name
        for n, v in self.parameters.items():
            tmp += '\n |%s=%s' % (n, v)
        if len(self.parameters) > 0:
            tmp += '\n'
        tmp += '}}'

        return tmp

    def wikitext(self):
        tmp = '{{%s' % self._name
        for n, v in self.parameters.items():
            tmp += '|%s=%s' % (n, v)
        tmp += '}}'


    # def save(self):
    #     self.node.xpath('title')[0].text = self._name
    #     parts = self.node.xpath('part')
    #     for key, param in self.parameters.items():
    #         i = unicode(param.index)
    #         n = unicode(param.name)

    #         fnd = False
    #         for part in parts:
    #             #print '"%s"  "%s"  "%s"' % (part.xpath('name')[0].get('index'), part.xpath('name')[0].text, n)

    #             if part.xpath('name')[0].get('index') == i or part.xpath('name')[0].text == n:
    #                 part.xpath('value')[0].text = param.value
    #                 fnd = True
    #         if not fnd:
    #             print ' ->! APPEND'
    #             self.node.append(etree.XML('<part><name>%s</name>=<value>%s</value></part>' % (n, param.value)))

            #print self.node.xpath('part/value')[0].text, '->', v
            #self.node.xpath('part/name')[0].text = n
            #self.node.xpath('part/value')[0].text = v


class TemplateEditor(object):

    def __init__(self, text):
        xml = preprocessToXml(text)
        parser = etree.XMLParser()
        self.text = text
        self.doc = etree.parse(StringIO(xml), parser)
        # root = self.doc.xpath('/root')[0]

        self.templates = Templates(self, self.doc)

        # self.scan_for_templates()

    def xml(self):
        # for key, val in self.templates.items():
        #     for tpl in val:
        #         tpl.save()
        return etree.tostring(self.doc)

    def wikitext(self):
        # for key, val in self.templates.items():
        #     for tpl in val:
        #         tpl.save()
        txt = get_wikitext(self.doc.xpath('/root')[0])
        return txt

if __name__ == "__main__":
    orig = 'LLorem {{ipsum|kake=bake}} {{{{{Min {{lille}} mal}}}son| sorona | Kake = sake }}'
    d = TemplateEditor(orig)
    print orig == d.wikitext()

    orig = 'LLorem {{IIIIIIIIIIIIIIIIIIIIIIII}'
    d = TemplateEditor(orig)
    print orig == d.wikitext()

    #print orig
    #print d.as_wikitext()

    #xml = '<root>LLorem ipsum <template><title><tplarg><title>Min lille mal</title></tplarg></title><part><name>Kake</name>=<value>sake</value></part></template></root>'
