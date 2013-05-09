#encoding=utf-8
from __future__ import unicode_literals
import unittest
import nose
from danmicholoparser import DanmicholoParseError, MainText


class TestTemplateEditor2(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple_template(self):
        # Check that a simple template is stripped
        text = 'Alfa {{beta}} gamma'
        te = MainText(text).maintext.split()
        self.assertEqual(len(te), 2)  # only two words should remain

    def test_recursive_tables(self):
        # Check that recursive tables are stripped correctly
        text = 'Alfa {| \n|beta \n{| \n|gamma \n|} \n|} delta'
        te = MainText(text).maintext.split()
        self.assertEqual(len(te), 2)  # only two words should remain


if __name__ == '__main__':
    unittest.main()
