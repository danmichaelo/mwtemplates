# encoding=utf-8
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
        if sys.version_info > (3, 0):
            self.assertEqual(type(te.templates['lang'][0].name).__name__, 'str')
        else:
            self.assertEqual(type(te.templates['lang'][0].name).__name__, 'unicode')

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

    def test_find_param_3(self):
        # Check using get_anonymous_parameters method
        text = 'Lorem ipsum {{lang|fr}} dolor sit amet'
        tpl = TemplateEditor(text).templates['lang'][0]
        params = tpl.get_anonymous_parameters()
        self.assertEqual(params[1], 'fr')

    def test_find_param_4(self):
        # Check that anonymous parameter can be found using alternative declaration method
        text = 'Lorem ipsum {{lang|1=fr}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertTrue(1 in e.templates['lang'][0].parameters)

    def test_find_param_5(self):
        # it should not be treated as a string
        text = 'Lorem ipsum {{lang|1=fr}} dolor sit amet'
        e = TemplateEditor(text)
        self.assertFalse('1' in e.templates['lang'][0].parameters)

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

    def test_change_template_name(self):
        # Check that a template can be renamed, with whitespace preserved
        text = 'Lorem ipsum {{ Infoboks A\n| maks=2\n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.name = 'Mal B'
        tmp = text.replace('Infoboks A', 'Mal B')
        self.assertEqual(dp.wikitext(), tmp)

    def test_edit_empty_parameter(self):
        # Check that an empty parameter can be edited
        text = 'Lorem ipsum {{ Infoboks A | date= | title= }} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['date'] = 'test'
        tmp = text.replace('date=', 'date=test')
        self.assertEqual(dp.wikitext(), tmp)

    def test_edit_empty_parameter_with_linebreak(self):
        # Check that an empty parameter can be edited, with linebreak preserved
        text = 'Lorem ipsum {{ Infoboks A \n| date= \n| title= \n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['date'] = 'test'
        tmp = text.replace('date= ', 'date= test')
        self.assertEqual(dp.wikitext(), tmp)

    def test_edit_nonempty_parameter(self):
        # Check that a parameter can be renamed, with whitespace preserved
        text = 'Lorem ipsum {{ Infoboks A\n| maks = 2 \n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['maks'] = '3'
        tmp = text.replace('2', '3')
        self.assertEqual(dp.wikitext(), tmp)

    def test_edit_nonempty_parameter_alternative(self):
        # Check that a parameter can be renamed using 'parameter.value='
        text = 'Lorem ipsum {{ Infoboks A\n| maks = 2 \n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['maks'].value = '3'
        tmp = text.replace('2', '3')
        self.assertEqual(dp.wikitext(), tmp)

    def test_edit_anonymous_parameter1(self):
        # Check that an anomyous parameter can be edited
        text = 'Lorem ipsum {{lang|fr}} amet'
        dp = TemplateEditor(text)
        dp.templates['lang'][0].parameters[1] = 'no'
        tmp = text.replace('fr', 'no')
        self.assertEqual(dp.wikitext(), tmp)

    def test_edit_anonymous_parameter2(self):
        # Check that an anomyous parameter can be edited, preserving declaration
        text = 'Lorem ipsum {{lang|1=fr}} amet'
        dp = TemplateEditor(text)
        dp.templates['lang'][0].parameters[1] = 'no'
        tmp = text.replace('fr', 'no')
        self.assertEqual(dp.wikitext(), tmp)

    def test_delete_parameter(self):
        # Check that a parameter can be renamed, with whitespace preserved
        text = 'Lorem ipsum {{ Infoboks A\n| maks = 2 \n}} dolor sit amet'
        text2 = 'Lorem ipsum {{ Infoboks A\n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        del templ.parameters['maks']
        self.assertEqual(dp.wikitext(), text2)

    def test_find_whitespace1(self):
        # Check that a whitespace pattern can be found
        text = 'Lorem ipsum {{ Infoboks A\n| a = 2 \n| b = 3 \n}} dolor sit amet'
        dp = TemplateEditor(text)
        name_ws, value_ws = dp.templates['infoboks A'][0].parameters.find_whitespace_pattern()
        self.assertEqual(' ', name_ws[0])
        self.assertEqual(' ', name_ws[1])
        self.assertEqual(' ', value_ws[0])
        self.assertEqual(' \n', value_ws[1])

    def test_add_parameter1(self):
        # Check that a parameter can be added, and that an existing whitespace pattern is followed
        text = 'Lorem ipsum {{ Infoboks A\n| a = 2 \n| b = 3 \n}} dolor sit amet'
        text2 = 'Lorem ipsum {{ Infoboks A\n| a = 2 \n| b = 3 \n| c = 4 \n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['c'] = '4'
        self.assertEqual(dp.wikitext(), text2)

    def test_add_parameter2(self):
        # Check that a parameter can be added, and that an existing whitespace pattern is followed
        text = 'Lorem ipsum {{ Infoboks A\n| maks = 2 \n}} dolor sit amet'
        text2 = 'Lorem ipsum {{ Infoboks A\n| maks = 2 \n| dato = TEST \n}} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['dato'] = 'TEST'
        self.assertEqual(dp.wikitext(), text2)

    def test_add_parameter3(self):
        # Check that a parameter can be added, and that an existing whitespace pattern is followed
        text = 'Lorem ipsum {{ Infoboks A | a = 2 }} dolor sit amet'
        text2 = 'Lorem ipsum {{ Infoboks A | a = 2 | b = 3 }} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        templ.parameters['b'] = '3'
        self.assertEqual(dp.wikitext(), text2)

    def test_delete_parameter(self):
        # Check that a parameter can be deleted
        text = 'Lorem ipsum {{ Infoboks A | a = 2 | b = 3 | c = 4 }} dolor sit amet'
        text2 = 'Lorem ipsum {{ Infoboks A | a = 2 | c = 4 }} dolor sit amet'
        dp = TemplateEditor(text)
        templ = dp.templates['infoboks A'][0]
        del templ.parameters['b']
        self.assertEqual(dp.wikitext(), text2)


if __name__ == '__main__':
    unittest.main()
