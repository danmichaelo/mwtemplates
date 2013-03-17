#encoding=utf-8
#from __future__ import unicode_literals

import unittest
from unittest.util import safe_repr
import logging
#import termstyle
import nose
from danmicholoparser import preprocessToXml

def htmlspecialchars(text):
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

class TestPreprocessor(unittest.TestCase):

    # def _baseAssertEqual(self, first, second, msg=None):
    #     """The default assertEqual implementation, not type specific."""
    #     if not first == second:
    #         standardMsg = '\n%s !=\n%s' % (termstyle.red(safe_repr(first)), termstyle.green(safe_repr(second)))
    #         msg = self._formatMessage(msg, standardMsg)
    #         raise self.failureException(msg)

    def setUp(self):
        pass

    def test_empty(self):
        with self.assertRaises(TypeError):
            preprocessToXml()

    def test_simple(self):
        text = 'Lorem ipsum'
        xml = preprocessToXml(text)
        correct_xml = '<root>%s</root>' % text
        self.assertEqual(xml, correct_xml)

    def test_linebreak(self):
        # Make sure preprocessor does not eat linebreaks
        text = '\n'
        xml = preprocessToXml(text)
        correct_xml = '<root>%s</root>' % text
        self.assertEqual(xml, correct_xml)

    def test_simple_template(self):
        name = 'Lorem ipsum'
        xml = preprocessToXml('{{%s}}' % name)
        correct_xml = '<root><template><title>%s</title></template></root>' % name
        self.assertEqual(xml, correct_xml)

    def test_nested_templates(self):
        args = ('Unus','Duo','Infinitas')
        text = '{{%s|{{%s|{{%s}}}}}}' % args
        xml = preprocessToXml('%s' % text)
        val = lambda name,val: '<template><title>%s</title>' % name + { '': '' }.get(val, '<part><name index="1" /><value>%s</value></part>' % val) + '</template>'
        correct_xml = '<root>' + val(args[0], val(args[1], val(args[2], ''))) + '</root>'
        self.assertEqual(xml, correct_xml)

    def test_template_with_tplarg(self):
        # A quite comlicated example, with a tplarg as the template name. This will also involve re-adding stack elements back into the stack after the }}}
        text = 'LLorem ipsum {{{{{Domino}}} | est = infinitus }}'
        xml = preprocessToXml(text)
        correct_xml = '<root>LLorem ipsum <template><title><tplarg><title>Domino</title></tplarg> </title><part><name> est </name>=<value> infinitus </value></part></template></root>'
        self.assertEqual(xml, correct_xml)

    def test_template_with_argument(self):
        name = 'Lorem ipsum'
        arg = 'dolores goppik'
        xml = preprocessToXml('{{%s|%s}}' % (name, arg))
        correct_xml = '<root><template><title>%s</title><part><name index="1" /><value>%s</value></part></template></root>' % (name, arg)
        self.assertEqual(xml, correct_xml)

    def test_simple_template_unicode(self):
        name = u'Lårem øpsum'
        xml = preprocessToXml('{{%s}}' % name)
        correct_xml = '<root><template><title>%s</title></template></root>' % name
        self.assertEqual(xml, correct_xml)

    def test_template_with_argument_unicode(self):
        name = u'ølipsum'
        arg = u'ål€en'
        xml = preprocessToXml('{{%s|%s}}' % (name, arg))
        correct_xml = '<root><template><title>%s</title><part><name index="1" /><value>%s</value></part></template></root>' % (name, arg)
        self.assertEqual(xml, correct_xml)

    def test_link(self):
        text = 'Lorem [[ipsum]]'
        xml = preprocessToXml('%s' % text )
        correct_xml = '<root>%s</root>' % text
        self.assertEqual(xml, correct_xml)

    def test_comment(self):
        text = 'Lorem <!-- ipsum -->'
        xml = preprocessToXml('%s' % text )
        correct_xml = '<root>%s</root>' % htmlspecialchars(text)
        self.assertEqual(xml, correct_xml)

    def test_comment_unclosed(self):
        text = 'Lorem <!-- ipsum '
        xml = preprocessToXml('%s' % text )
        correct_xml = '<root>%s</root>' % htmlspecialchars(text)
        self.assertEqual(xml, correct_xml)

    def test_tag_unclosed(self):
        tpl = 'ipsum'
        text = 'Lorem <div>'
        xml = preprocessToXml('%s{{%s}}' % (text, tpl) )
        correct_xml = '<root>%s<template><title>%s</title></template></root>' % (htmlspecialchars(text), tpl)
        self.assertEqual(xml, correct_xml)

    def test_unclosed_template1(self):
        # Leaving out one end brace
        name = '{{Lorem ipsum}'
        xml = preprocessToXml('%s' % name)
        correct_xml = '<root>%s</root>' % name
        self.assertEqual(xml, correct_xml)

    def test_unclosed_template2(self):
        # Leaving out both end braces
        name = '{{Lorem ipsum'
        xml = preprocessToXml('%s' % name)
        correct_xml = '<root>%s</root>' % name
        self.assertEqual(xml, correct_xml)
        
    def test_template_in_comment(self):
        # The template should not be handled if inside a comment
        text = 'Lorem <!--{{ipsum}}-->'
        xml = preprocessToXml('%s' % text )
        correct_xml = '<root>%s</root>' % htmlspecialchars(text)
        self.assertEqual(xml, correct_xml)

    def test_template_in_nowiki(self):
        # The template should not be handled if inside <nowiki>
        text = 'Lorem <nowiki>{{ipsum}}</nowiki>'
        xml = preprocessToXml('%s' % text )
        correct_xml = '<root>%s</root>' % htmlspecialchars(text)
        self.assertEqual(xml, correct_xml)

    def test_template_in_and_after_nowiki(self):
        # The template should not be handled if inside <nowiki>
        text = 'Lorem <nowiki>{{ipsum}}</nowiki>{{ipsum}}'
        xml = preprocessToXml(text)
        correct_xml = '<root>Lorem &lt;nowiki&gt;{{ipsum}}&lt;/nowiki&gt;<template><title>ipsum</title></template></root>'
        self.assertEqual(xml, correct_xml)

    def test_template_in_math(self):
        # The template should not be handled if inside <math>
        text = 'Lorem <math>{{ipsum}}</math>'
        xml = preprocessToXml('%s' % text )
        correct_xml = '<root>%s</root>' % htmlspecialchars(text)
        self.assertEqual(xml, correct_xml)

    def test_html_tags1(self):
        text = 'Lorem<br />ipsum'
        xml = preprocessToXml(text)
        correct_xml = '<root>Lorem&lt;br /&gt;ipsum</root>'
        self.assertEqual(xml, correct_xml)

    def test_html_tags2(self):
        text = 'Lorem<b>ipsum</b> ipsam'
        xml = preprocessToXml(text)
        correct_xml = '<root>Lorem&lt;b&gt;ipsum&lt;/b&gt; ipsam</root>'
        self.assertEqual(xml, correct_xml)

if __name__ == '__main__':
    unittest.main()
