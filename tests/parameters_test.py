# encoding=utf-8
from __future__ import unicode_literals
import unittest
import sys
import os
import mock
import pytest
from mwtemplates.templateeditor2 import Parameters


class TestParameters(unittest.TestCase):

    def setUp(self):
        self.template = mock.MagicMock()
        self.params = Parameters(self.template)

    def addParam(self, key, value=None):
        p = mock.MagicMock()
        p.key = key
        p.value = value
        self.params._entries.append(p)
        return p

    def test_get(self):
        param1 = self.addParam('some existing param')
        params = self.params

        assert self.params.get('some nonexisting param') is None
        with pytest.raises(KeyError):
            params['some nonexisting param']

        assert params.get('some nonexisting param', 'some default value') == 'some default value'

        assert params.get('some existing param') == param1
        assert params['some existing param'] == param1

    def test_contains(self):
        param1 = self.addParam('some param')
        params = self.params

        assert 'some param' in params
        assert 'some other param' not in params
        assert param1 in params

    def test_items(self):
        param1 = self.addParam('key1')
        param2 = self.addParam('key2')
        param3 = self.addParam('key2')
        params = self.params

        keys = params.keys()
        assert len(keys) == 3
        assert keys == ['key1', 'key2', 'key2']

        items = params.items()
        assert len(items) == 3
        assert items[0][0] == 'key1'
        assert items[1][0] == 'key2'
        assert items[2][0] == 'key2'

        items = [x for x in params.iteritems()]
        assert len(items) == 3
        assert items[0][0] == 'key1'
        assert items[1][0] == 'key2'
        assert items[2][0] == 'key2'

        items = [x for x in params]
        assert len(items) == 3
        assert items[0] == param1
        assert items[1] == param2
        assert items[2] == param3

    def test_setitem(self):
        param1 = self.addParam('key1')
        params = self.params

        params['key1'] = 'some value'

        param1.edit.assert_called_once_with('some value')

    def test_index(self):
        param1 = self.addParam('key1')
        param2 = self.addParam('key2')
        param3 = self.addParam('key2')
        params = self.params

        assert params.index(param1) == 0
        assert params.index(param2) == 1
        assert params.index(param3) == 2

    def test_delitem(self):
        param1 = self.addParam('key1')
        params = self.params

        assert len(params.keys()) == 1
        del params['key1']
        assert len(params.keys()) == 0

        self.template.node.remove.assert_called_once_with(mock.ANY)

    def test_remove(self):
        param1 = self.addParam('key1')
        param2 = mock.MagicMock()  # not added
        params = self.params

        assert len(params.keys()) == 1
        params.remove(param1)
        assert len(params.keys()) == 0

        with pytest.raises(ValueError):
            params.remove(param2)

        self.template.node.remove.assert_called_once_with(mock.ANY)
