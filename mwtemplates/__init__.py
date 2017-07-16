# encoding=utf-8
"""
mwtemplates
Copyright (c) 2012-2016 Dan Michael O. Heggø

Simple wikitext template parser and editor
"""

from mwtemplates.templateeditor2 import TemplateEditor
from mwtemplates.preprocessor import preprocessToXml, NowikiError

# Logging: Add a null handler to avoid "No handler found" warnings.
import logging
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
