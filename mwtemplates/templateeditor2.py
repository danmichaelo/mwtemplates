#encoding=utf-8
"""
mwtemplates
Copyright (c) 2012-2013 Dan Michael O. Heggø

Simple wikitext template parser and editor
"""

from __future__ import unicode_literals
from __future__ import print_function
import sys

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
try:
    from io import StringIO  # Python 3
except ImportError:
    from StringIO import StringIO  # Python 2
from mwtemplates.preprocessor import preprocessToXml

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class TemplateParseError(Exception):
    pass


def most_common(lst):
    return max(set(lst), key=lst.count)


def get_whitespace(txt):
    """
    Returns a list containing the whitespace to the left and
    right of a string as its two elements
    """

    # if the entire parameter is whitespace
    rall = re.search(r'^([\s])+$', txt)
    if rall:
        tmp = txt.split('\n', 1)
        if len(tmp) == 2:
            return (tmp[0], '\n' + tmp[1])
        else:
            return (tmp, '')
    left = ''
    # find whitespace to the left of the parameter
    rlm = re.search(r'^([\s])+', txt)
    if rlm:
        left = rlm.group(0)
    right = ''
    # find whitespace to the right of the parameter
    rrm = re.search(r'([\s])+$', txt)
    if rrm:
        right = rrm.group(0)
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
            raise TemplateParseError("Found unknown tag: %s"
                                     % etree.tostring(child))
        if child.tail is not None:
            tmp += child.tail
    return tmp


#def get_arg(node):
#    node.xpath('name')[0]
#    node.xpath('value')[0]


class Templates(object):
    """
    Dictionary-like class to hold templates.
    The first character of the key is case-insensitive, to mimic MediaWiki,
    where {{Hello}} and {{hello}} are considered the same template, while
    {{Hello}} and {{HEllo}} are not.
    """

    def __init__(self, editor, doc):
        self.editor = editor
        self.doc = doc
        #self._entries = self._templates()

    def _templates(self):
        templates = []
        for node in self.doc.findall('.//template'):
            templates.append(Template(node, self.editor))
        return templates

    # def add(self, node):
    #     self._entries.append(Template(node, self.editor))

    def __contains__(self, tpl_name):
        tpl_name = tpl_name[0].upper() + tpl_name[1:]
        for tpl in self._templates():
            if tpl.key == tpl_name:
                return True
        return False

    def __getitem__(self, tpl_name):
        tpl_name = tpl_name[0].upper() + tpl_name[1:]
        return [tpl for tpl in self._templates() if tpl.key == tpl_name]
        #raise KeyError

    def __repr__(self):
        return self._templates().__repr__()

    def __len__(self):
        return len(self._templates())

    def keys(self):
        return list(set([tpl.key for tpl in self._templates()]))

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def iteritems(self):
        for key in self.keys():
            yield (key, self[key])

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
    """
    Dictionary-like class to hold a template's parameters.
    """

    def __init__(self, template):
        self._entries = []
        self.template = template

    def __contains__(self, param_name):
        for param in self._entries:
            if param.key == param_name:
                return True
        return False

    def __getitem__(self, param_name):
        for param in self._entries:
            if param.key == param_name:
                return param
        raise KeyError

    def __setitem__(self, name, val):
        # python2   <->  python3
        # 'unicode' <-> 'str'
        # 'str'     <-> 'bytes'
        if type(val).__name__ in ['unicode', 'str', 'bytes' 'int']:
            for entry in self._entries:
                if entry.key == name:
                    # parameter changed:
                    entry.edit(val)
                    return
            # new parameter:
            name_ws, value_ws = self.find_whitespace_pattern()
            #print '"' + whitespace[0] + '", "' + whitespace[1] + '"'
            name = name_ws[0] + name + name_ws[1]
            val = value_ws[0] + val + value_ws[1]
            parentnode = self.template.node
            node = etree.XML('<part><name>%s</name>=<value>%s</value></part>'
                             % (name, val))
            parentnode.append(node)
            self.add(node)
        else:
            raise TypeError

    def __delitem__(self, param_name):
        for i, entry in enumerate(self._entries):
            if entry.key == param_name:
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

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        for param in self._entries:
            yield param

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
    """
    Class to hold a single template parameter.
    """

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
        logger.debug('  added parameter: %s=%s',
                     self._name.strip(), self._value.strip())

    def edit(self, val):
        logger.debug('Parameter "%s" changed: "%s" -> "%s"',
                     self.key, self.value.strip(), val)
        whitespace = get_whitespace(self._value)
        self._value = whitespace[0] + val + whitespace[1]
        # self.node.xpath('value')[0].text = self._value
        self.node.replace(self.node.xpath('value')[0],
                          etree.XML('<value>' + self._value + '</value>'))

    #@property
    #def index(self):
    #    return self._index

    @property
    def name(self):
        return self._name

    @property
    def key(self):
        if self._index != -1:
            return self._index
        else:
            tmp = self.name.strip()
            if tmp.isnumeric():
                return int(tmp)
            else:
                return tmp

    @property
    def value(self):
        return self._value.strip()

    def __eq__(self, param):
        if type(param).__name__ == 'unicode':
            return self.__unicode__() == param
        elif type(param).__name__ == 'str':
            return self.__str__() == param
        elif type(param).__name__ == 'int':
            return int(self.__unicode__()) == param
        else:
            return False

    def __ne__(self, param):
        return not self.__eq__(param)

    def __unicode__(self):
        return self._value.strip()

    def __str__(self):
        if sys.version_info > (3, 0):
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf-8')

    def __float__(self):
        return float(self.__unicode__())

    def __int__(self):
        return int(self.__unicode__())

    def __repr__(self):
        return self._value.strip()


class Template(object):
    """
    Class to hold a single template.
    """

    def __init__(self, node, editor):

        logger.debug('TemplateEditor got new template')

        self.node = node
        self.editor = editor
        self._name = ''
        self.parameters = Parameters(self)
        for elem in node:
            if elem.tag == 'title':
                self._name = get_wikitext(elem)
                logger.debug('  name: %s', self.name)
            elif elem.tag == 'part':
                self.parameters.add(elem)

    def __repr__(self):
        return self.key

    @property
    def key(self):
        tmp = self._name.strip()
        tmp = re.sub(r'^(?:[Mm]al|[Tt]emplate):', '', tmp)
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
        """
        Returns the anonymous (non-named) parameters as a normal list, but with
        indices starting on 1, not 0, to comply with standard mediawiki practice.
        """
        tmp = {}
        for param in self.parameters:
            if type(param.key) == int:
                tmp[param.key] = param.value
        lst = [None]
        for param in range(1, max(tmp.keys()) + 1):
            lst.append(tmp[param])
        return lst

    def __unicode__(self):
        tmp = '{{%s' % self.name
        for param in self.parameters:
            tmp += '\n |%s=%s' % (param.key, param.value)
        if len(self.parameters) > 0:
            tmp += '\n'
        tmp += '}}'

        return tmp

    def __str__(self):
        if sys.version_info > (3, 0):
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf-8')

    def remove(self):
        self.__del__()

    def __del__(self):
        logger.debug('Removing node "%s"', self.key)
        parent = self.node.getparent()
        prevnode = None
        for node in parent.getchildren():
            if node == self.node:
                if prevnode is None:
                    if parent.text is None:
                        parent.text = self.node.tail.lstrip()
                    else:
                        parent.text += self.node.tail.lstrip()

                else:
                    if prevnode.tail is None:
                        prevnode.tail = self.node.tail.lstrip()
                    else:
                        prevnode.tail += self.node.tail.lstrip()
                parent.remove(self.node)
                return
            else:
                prevnode = node


class TemplateEditor(object):
    r"""
    TemplateEditor is the main class to work with templates in some wikitext.

    Example:

    >>> wikitext = '{{infobox country\n' \
    ...    + '|name=Fantasia\n' \
    ...    + '|population_census=4,830,300 }}'
    >>> editor = TemplateEditor(wikitext)
    >>> tpl = editor.templates['Infobox country'][0]
    >>> tpl.parameters['population_census'] = '5,033,676'
    >>> print(editor.wikitext())
    {{infobox country
    |name=Fantasia
    |population_census=5,033,676 }}
    """

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
