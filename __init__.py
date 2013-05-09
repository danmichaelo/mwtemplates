# encoding=utf-8
"""
DanmicholoParser
Copyright (c) 2012-2013 Dan Michael O. Heggø

Simple wikitext template parser and editor
"""

from danmicholoparser.dperrors import DanmicholoParseError
from danmicholoparser.templateeditor2 import TemplateEditor 
from danmicholoparser.preprocessor import preprocessToXml
from danmicholoparser.maintext import MainText, condition_for_soup
