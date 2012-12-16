#encoding=utf-8
from __future__ import unicode_literals
import unittest
import mwclient
import random
import logging
from danmicholoparser import DanmicholoParseError, TemplateEditor

class TestTemplateEditor(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger() # root logger
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler('templateeditor-test.log', mode='w', encoding='utf-8')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    
    def test_find_template(self):
        # Check that templates can be found
        text = 'Lorem ipsum {{lang}} dolor sit amet'
        dp = TemplateEditor(text)
        self.assertTrue('lang' in dp.templates)

    def test_find_param_1(self):
        # Check that anonymous parameter can be found
        text = 'Lorem ipsum {{lang|fr}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertTrue(1 in e.templates['lang'][0].parameters)
    
    def test_find_param_2(self):
        # but not when not present
        text = 'Lorem ipsum {{lang}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertFalse(1 in e.templates['lang'][0].parameters)
    
    def test_has_param_2(self):
        # has_param() should return true if non-empty
        text = 'Lorem ipsum {{lang|fr}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertTrue(e.templates['lang'][0].has_param(1))

    def test_has_param_1(self):
        # has_param() should return false if empty (contains only whitespace)
        text = 'Lorem ipsum {{lang| \t\n}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertFalse(e.templates['lang'][0].has_param(1))
    
    def test_emptyparam1(self):
        # Check that the parser doesn't strip off empty parameters:
        text = '{{some template|}}'
        e = TemplateEditor(text)
        self.assertTrue(1 in e.templates['some template'][0].parameters)

    def test_emptyparam2(self):
        # Check that the parser doesn't strip off empty parameters:
        text = '{{some template||}}'
        e = TemplateEditor(text)
        para = e.templates['some template'][0].parameters
        self.assertTrue(1 in para and 2 in para)
    
    def test_multibyte_1(self):
        # Check handling of multibyte chars (remember unicode_literals!)
        text = 'Lorem ipsum {{Infoboks æøåß|ål=2}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertTrue('infoboks æøåß' in e.templates)
    
    def test_multibyte_2(self):
        # Check handling of multibyte chars (remember unicode_literals!)
        text = 'Lorem ipsum {{Infoboks æøåß|ål=2}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertEqual(e.templates['infoboks æøåß'][0].parameters['ål'], '2')
    
    def test_arabic(self):
        # Check handling of multibyte chars, unicode level 2
        text = 'Lorem ipsum {{Infoboks العربية}} dolor sit amet'
        dp = TemplateEditor(text)
        t = dp.templates
        self.assertEqual(text, dp.get_wikitext())
    
    def test_onlywhitespace(self):
        # Check that the parser doesn't strip off empty parameters:
        text = '{{some template |   | someval=true}}'
        dp = TemplateEditor(text)
        p = dp.templates['some template'][0].parameters
        self.assertEqual(text, dp.get_wikitext())
    
    def test_insidetag(self):
        # Check that the parser doesn't strip off empty parameters:
        text = '<ref>[{{some template|maks=2}}]</ref>'
        dp = TemplateEditor(text)
        self.assertTrue(dp.templates['some template'][0].has_param('maks'))
    
    def test_namechange(self):
        # Check that a template can be renamed, with whitespace preserved
        text = 'Lorem ipsum {{ Infoboks A\n| maks=2\n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks a'][0]
        templ.name = 'Mal B'
        tmp = text.replace('Infoboks A', 'Mal B')
        self.assertEqual(dp.get_wikitext(), tmp)
    
    def test_doubleparam(self):
        # should fail if the same named parameter is passed twice to a template
        text = 'Lorem ipsum {{ Infoboks A\n| maks=2 |maks=3\n}} dolor sit amet'
        dp = TemplateEditor(text)
        self.assertRaises(DanmicholoParseError, dp.get_templates)

    def test_ignorecomments(self):
        # should not parse templates within comments
        text = 'Lorem ipsum <!--{{flagg|no}}--> dolor sit amet'
        dp = TemplateEditor(text)
        self.assertEqual(len(dp.templates.keys()), 0)
    
    def test_commentswithintemplates(self):
        arg = '<!-- kommentartest -->'
        text = 'Lorem ipsum {{flagg\n|land=%s|param2=test\n }} dolor sit amet' % arg
        dp = TemplateEditor(text)
        self.assertEqual(dp.templates['flagg'][0].parameters['land'], arg)
    
    def test_ignore_nowiki(self):
        text = '<nowiki>{{flagg|no}}</nowiki>'
        dp = TemplateEditor(text)
        self.assertEqual(len(dp.templates.keys()), 0)
    
    def test_parametersintemplates(self):
        arg = '{{{1|{{{2}}}}}}'
        text = 'Lorem ipsum {{flagg|land=%s}} dolor sit amet' % arg
        dp = TemplateEditor(text)
        self.assertEqual(dp.templates['flagg'][0].parameters['land'], arg)


if __name__ == '__main__':
    unittest.main()

