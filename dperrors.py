# encoding=utf-8

class DanmicholoParseError(Exception):

    def __init__(self, msg):
        self.msg = msg
        self.parse_errors = []
