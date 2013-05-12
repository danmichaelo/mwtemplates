#encoding=utf-8
from __future__ import unicode_literals
import unittest
import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from mwtemplates import TemplateEditor


class TestTemplateEditor2(unittest.TestCase):

    def setUp(self):
        pass

    def test_find_template(self):
        # Check that templates can be found
        text = 'Lorem ipsum {{lang}} dolor sit amet'
        te = TemplateEditor(text)
        self.assertTrue('lang' in te.templates)

    def test_name_is_unicode(self):
        # Check that templates can be found
        text = 'Lorem ipsum {{lang}} dolor sit amet'
        te = TemplateEditor(text)
        self.assertEqual(type(te.templates['lang'][0].name), unicode)

    def test_template_name(self):
        # Check that templates can be found
        text = 'Lorem ipsum {{lang}} dolor sit amet'
        te = TemplateEditor(text)
        self.assertEqual(te.templates['lang'][0].name, 'Lang')

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
        self.assertEqual(text, dp.wikitext())

    def test_onlywhitespace(self):
        # Check that the parser doesn't strip off empty parameters:
        text = '{{some template |   | someval=true}}'
        dp = TemplateEditor(text)
        self.assertEqual(text, dp.wikitext())

    def test_insidetag(self):
        # Check that the parser doesn't strip off empty parameters:
        text = '<ref>[{{some template|maks=2}}]</ref>'
        dp = TemplateEditor(text)
        self.assertTrue(dp.templates['some template'][0].has_param('maks'))

    def test_ignorecomments(self):
        # should not parse templates within comments
        text = 'Lorem ipsum <!--{{flagg|no}}--> dolor sit amet'
        dp = TemplateEditor(text)
        self.assertEqual(len(dp.templates), 0)

    def test_commentswithintemplates(self):
        arg = '<!-- kommentartest -->'
        text = 'Lorem ipsum {{flagg\n|land=%s|param2=test\n }} dolor' % arg
        dp = TemplateEditor(text)
        self.assertEqual(dp.templates['flagg'][0].parameters['land'], arg)

    def test_ignore_nowiki(self):
        text = '<nowiki>{{flagg|no}}</nowiki>'
        dp = TemplateEditor(text)
        self.assertEqual(len(dp.templates), 0)

    def test_edit_nowiki(self):
        text = '<nowiki>{{flagg|no}}</nowiki>{{flagg|%s}}'
        dp = TemplateEditor(text % 'no')
        dp.templates['flagg'][0].parameters[1] = 'en'
        self.assertEqual(dp.wikitext(), text % 'en')

    def test_parametersintemplates(self):
        arg = '{{{1|{{{2}}}}}}'
        text = 'Lorem ipsum {{flagg|land=%s}} dolor sit amet' % arg
        dp = TemplateEditor(text)
        self.assertEqual(dp.templates['flagg'][0].parameters['land'], arg)

    def test_malprefix(self):
        text = 'Lorem ipsum {{Mal:Flagg}} og {{Template:Flagg}} og {{Flagg}}.'
        dp = TemplateEditor(text)
        self.assertEqual(len(dp.templates['flagg']), 3)

    def test_nested_templates(self):
        text = 'Lorem{{templ1|arg={{templ2|20}}}}'
        dp = TemplateEditor(text)
        self.assertEqual(text, dp.wikitext())

    def test_get_anonymous_parameters(self):
        text = 'Lorem {{Ipsum|dolor|sit|amet}}'
        te = TemplateEditor(text)
        tpl = te.templates['ipsum'][0]
        self.assertEqual(len(tpl.get_anonymous_parameters()), 4)

    def test_get_keys(self):
        text = 'Lorem {{Ipsum|dolor|sit|amet}}'
        te = TemplateEditor(text)
        tpl = te.templates.keys()
        self.assertEqual(tpl, ['Ipsum'])

    def test_get_items(self):
        text = 'Lorem {{Ipsum|dolor|sit|amet}}'
        te = TemplateEditor(text)
        x = te.templates.items()
        self.assertEqual(x[0][0], 'Ipsum')

    # MODIFICATION TESTS

    def test_namechange(self):
        # Check that a template can be renamed, with whitespace preserved
        text = 'Lorem ipsum {{ Infoboks A\n| maks=2\n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.name = 'Mal B'
        tmp = text.replace('Infoboks A', 'Mal B')
        self.assertEqual(dp.wikitext(), tmp)

    def test_paramchange(self):
        # Check that a parameter can be renamed, with whitespace preserved
        text = 'Lorem ipsum {{ Infoboks A\n| maks = 2 \n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['maks'] = '3'
        tmp = text.replace('2', '3')
        self.assertEqual(dp.wikitext(), tmp)

if __name__ == '__main__':
    unittest.main()
