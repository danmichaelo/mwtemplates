# encoding=utf-8
"""
DanmicholoParser
Copyright (c) 2012-2013 Dan Michael O. Heggø

Simple wikitext template parser and editor
"""


class DanmicholoParseError(Exception):
    """ Class for parse errors """

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
        self.parse_errors = []
