#encoding=utf-8
from __future__ import unicode_literals

# /Users/danmichael/code/mediawiki/core/includes/parser/Preprocessor_DOM.php
import re
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# First we define a few useful functions from PHP:


def strspn(str1, str2, start=0, length=-1):
    str2 = re.escape(str2)
    if length == -1:
        m = re.match(r'^([' + str2 + ']*)', str1[start:])
    else:
        m = re.match(r'^([' + str2 + ']{,' + str(length) + '})', str1[start:])
    if m:
        return len(m.group(1))
    else:
        return 0


def strcspn(str1, str2, start=0, length=-1, debug=False):
    str2 = re.escape(str2)
    if length == -1:
        m = re.match(r'^([^' + str2 + ']*)', str1[start:])
    else:
        m = re.match(r'^([^' + str2 + ']{,' + str(length) + '})', str1[start:])
    if m:
        return len(m.group(1))
    else:
        return 0


def htmlspecialchars(text):
    return text.replace("&", "&amp;") \
               .replace('"', "&quot;") \
               .replace("<", "&lt;") \
               .replace(">", "&gt;")


class PPDStack(object):

    def __init__(self):
        self.stack = []
        self.rootAccum = ''

    @property
    def top(self):
        if len(self.stack) == 0:
            return False
        else:
            return self.stack[-1]

    @property
    def accum(self):
        if self.top is False:
            return self.rootAccum
        else:
            return self.top.accum

    @accum.setter
    def accum(self, value):
        if self.top is False:
            self.rootAccum = value
        else:
            self.top.accum = value

    def count(self):
        return len(self.stack)

    def getCurrentPart(self):
        if self.top is False:
            return False
        else:
            return self.top.getCurrentPart()

    def append(self, data):
        if type(data) == PPDStackElement:
            self.stack.append(data)
        else:
            self.stack.append(PPDStackElement(data))
        logger.debug('+ Adding to stack: %s...',
                     self.top.data['open'] * self.top.data['count'])

    def pop(self):
        logger.debug('- Popping from stack: ...%s',
                     self.top.data['close'] * self.top.data['count'])
        return self.stack.pop()

    def addPart(self, s=''):
        self.top.addPart(s)

    def getFlags(self):
        if len(self.stack) == 0:
            return {'findEquals': False, 'findPipe': False, 'inHeading': False}
        else:
            return self.top.getFlags()


class PPDStackElement(object):

    def __init__(self, data):
        self.data = data
        self.parts = [PPDPart()]

    @property
    def accum(self):
        return self.parts[-1].out

    @accum.setter
    def accum(self, value):
        self.parts[-1].out = value

    def addPart(self, s=''):
        self.parts.append(PPDPart(s))

    def getCurrentPart(self):
        return self.parts[-1]

    def getFlags(self):
        partCount = len(self.parts)
        findPipe = self.data['open'] != '\n' and self.data['open'] != '['
        return {
            'findPipe': findPipe,
            'findEquals': findPipe and partCount > 1 and not 'eqpos' in self.parts[-1],
            'inHeading': self.data['open'] == r'\n'
        }

    # Get the output string that would result if the close is not found.
    def breakSyntax(self, openingCount=False):
        if self.data['open'] == '\n':
            s = self.parts[0]
        else:
            if openingCount is False:
                openingCount = self.data['count']
            s = self.data['open'] * openingCount
            first = True
            for part in self.parts:
                if first:
                    first = False
                else:
                    s += '|'
                s += part.out
        return s


class PPDPart(dict):
    # Optional member variables:
    #   eqpos       Position of equals sign in output accumulator
    #   commentEnd  Past-the-end input pointer for the last comment encountered
    #   visualEnd   Past-the-end input pointer for the end of the accumulator
    #               minus comments

    def __init__(self, out=''):
        self['out'] = out

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


def preprocessToXml(text):

    if type(text).__name__ != 'unicode' and type(text).__name__ != 'str':
        raise StandardError("preprocessToXml only accepts unicode or str")

    rules = {
        '{': {
            'end': '}',
            'names': {
                2: 'template',
                3: 'tplarg',
            },
            'min': 2,
            'max': 3
        },
        '[': {
            'end': ']',
            'names': {
                2: None
            },
            'min': 2,
            'max': 2
        }
    }

    # tja..
    xmlishRegex = '|'.join(['math', 'nowiki'])

    # Use "A" modifier (anchored) instead of "^", because ^ doesn't work
    # with an offset
    # DM: A is not available in Python, so let's try ^
    elementsRegex = re.compile(r'^(%s)(?:\s|\/>|>)|(!--)' % xmlishRegex,
                               flags=re.I)
    #r'~(%s)(?:\s|\/>|>)|(!--)~iA' % xmlishRegex

    stack = PPDStack()
    searchBase = '[{<'     # removed \n for now
    lengthText = len(text)

    stack.accum = '<root>'        # Current accumulator
    findEquals = False            # True to find equals signs in arguments
    findPipe = False              # True to take notice of pipe characters
    noMoreGT = False              # True if there are no more greater-than (>)
                                  # signs right of $i

    cnt = 0
    i = 0       # Input pointer, points to a pseudo-newline before start
    while True:
        cnt += 1
        if cnt > 100000:
            raise StandardError('Too long input. Aborting')

        # if fakeLineStart:
        #     found = 'line-start'
        #     curChar = ''
        # else:
        # Find next opening brace, closing brace or pipe
        search = searchBase
        #found = ''
        if stack.top is False:
            currentClosing = ''
        else:
            #print stack.top.data
            currentClosing = stack.top.data['close']
            search += currentClosing

        if findPipe:
            search += '|'
        if findEquals:
            # First equals will be for the template
            search += '='

        rule = None
        # Output literal section, advance input counter
        logger.debug('  [%4d] Advancing pointer until: %s', i,
                     search.replace('\n', '\\n'))
        literalLength = strcspn(text, search, i, debug=True)
        if literalLength > 0:
            stack.accum += htmlspecialchars(text[i:i + literalLength])
            logger.debug('  [%4d] Found literal section of length %d: "%s"',
                         i, literalLength, text[i:i + literalLength])
            i += literalLength

        if i >= len(text):
            # if currentClosing == "\n":
            #     # Do a past-the-end run to finish off the heading
            #     curChar = '';
            #     found = 'line-end';
            # else:
                # All done
                logger.debug('  [%4d] Reached the end (%d chars)',
                             i, len(text))
                break
        else:
            curChar = text[i]
            if curChar == '|':
                found = 'pipe'
            elif curChar == '=':
                found = 'equals'
            elif curChar == '<':
                found = 'angle'
            # elif curChar == r'\n':
            #     if inHeading:
            #         found = 'line-end'
            #     else:
            #         found = 'line-start'
            elif curChar == currentClosing:
                found = 'close'
            elif curChar in rules:
                found = 'open'
                rule = rules[curChar]
            else:
                i += 1
                continue

            if found == 'angle':
                matches = False

                # Determine element name
                matches = elementsRegex.match(text[i + 1:])
                if matches is None:
                    # Element name missing or not listed
                    logger.debug('  [%4d] Found tag with element name missing'
                                 + ' or not listed (excerpt: %s...)',
                                 i, text[i + 1:i + 1 + 10])
                    stack.accum += '&lt;'
                    i += 1
                    continue

                # Handle comments:
                # DM: We handle comments a bit differently than the original
                # PHP preprocessor. We just output them as they are, instead of
                # wrapping them in <comment> and htmlspecialchar-ize them.
                if matches.lastindex >= 2 and matches.group(2) == '!--':
                    # To avoid leaving blank lines, when a comment is both
                    # preceded and followed by a newline (ignoring spaces),
                    # trim leading and trailing spaces and one of the newlines.

                    # Find the end
                    endPos = text.find('-->', i + 4)
                    if endPos == -1:
                        # Unclosed comment in input, runs to end
                        inner = text[i:]
                        # Original code: stack.accum += '<comment>' +
                        # htmlspecialchars(inner) + '</comment>'
                        stack.accum += htmlspecialchars(inner)
                        i = lengthText
                    else:
                        startPos = i
                        endPos += 2
                        i = endPos + 1
                        inner = text[startPos:endPos + 1]
                        stack.accum += htmlspecialchars(inner)
                    continue

                name = matches.group(1)
                attrStart = i + len(name) + 1
                logger.debug('  [%4d] Found xml tag: %s', i, name)

                # Find end of tag
                tagEndPos = -1 if noMoreGT else text.find('>', attrStart)
                if tagEndPos == -1:
                    # Infinite backtrack
                    # Disable tag search to prevent worst-case O(N^2)
                    # performance
                    logger.debug('infinite backtrack')
                    noMoreGT = True
                    stack.accum += '&lt;'
                    i += 1
                    continue

                if text[tagEndPos - 1] == '/':
                    attrEnd = tagEndPos - 1
                    inner = ''
                    i = tagEndPos + 1
                    close = ''
                else:
                    attrEnd = tagEndPos
                    # Find closing tag
                    matches = re.search('<\/%s\s*>' % re.escape(name),
                                        text[tagEndPos + 1:])
                    if matches:
                        inner = text[tagEndPos + 1:tagEndPos + 1 + matches.start()]
                        i = tagEndPos + 1 + matches.start() \
                            + len(matches.group(0))
                        close = matches.group(0)
                    else:
                        # No end tag -- let it run out to the end of the text
                        logger.debug('         No end tag found')
                        inner = text[tagEndPos + 1:]
                        i = lengthText
                        close = ''

                if attrEnd <= attrStart:
                    attr = ''
                else:
                    attr = text[attrStart:attrEnd]

                tmp = (htmlspecialchars(name), htmlspecialchars(attr),
                       htmlspecialchars(inner), htmlspecialchars(close))
                stack.accum += '&lt;%s%s&gt;%s%s' % tmp

            elif found == 'open':
                # count opening brace characters
                count = strspn(text, curChar, i)
                #print "Found %d open braces" % count

                # we need to add to stack only if opening brace count
                # is enough for one of the rules
                if count >= rule['min']:

                    # Add it to the stack
                    piece = {
                        'open': curChar,
                        'close': rule['end'],
                        'count': count,
                        'lineStart': (i > 0 and text[i - 1] == r'\n')
                    }
                    stack.append(piece)
                    flags = stack.getFlags()
                    findPipe = flags['findPipe']
                    findEquals = flags['findEquals']

                else:
                    stack.accum += curChar * count

                i += count

            elif found == 'close':
                piece = stack.top
                # lets check if there are enough characters for closing brace
                maxCount = piece.data['count']
                count = strspn(text, curChar, i, maxCount)
                logger.debug('  [%4d] Found %d of %d close braces',
                             i, count, maxCount)

                # check for maximum matching characters (if there are 5
                # closing characters, we will probably need only
                # 3 - depending on the rules)
                rule = rules[piece.data['open']]
                if count > rule['max']:
                    # The specified maximum exists in the callback array,
                    # unless the caller has made an error
                    matchingCount = rule['max']
                else:
                    # Count is less than the maximum. Skip any gaps in the
                    # callback array to find the true largest match
                    # Need to use array_key_exists not isset because the
                    # callback can be null
                    matchingCount = count
                    while matchingCount > 0 \
                            and matchingCount not in rule['names'].keys():
                        matchingCount -= 1

                if matchingCount <= 0:
                    # No matching element found in callback array
                    # Output a literal closing brace and continue

                    #$accum .= htmlspecialchars(str_repeat($curChar,$count));
                    stack.accum += curChar * count
                    logger.debug('         ... which is not enough for'
                                 + ' current rule. Continuing...')

                    i += count
                    continue

                name = rule['names'][matchingCount]
                if name is None:
                    # No element, just literal text
                    element = piece.breakSyntax(matchingCount) \
                        + rule['end'] * matchingCount

                else:
                    # Create XML element
                    # Note: $parts is already XML, does not need to be encoded
                    parts = piece.parts
                    # print type(parts)
                    # logger.debug('%s', ', '.join([p for p in parts]))
                    title = parts[0].out
                    del parts[0]

                    # The invocation is at the start of the line if lineStart
                    # is set in the stack and all opening brackets are used up
                    if maxCount == matchingCount and piece.data['lineStart']:
                        attr = ' lineStart="1"'
                    else:
                        attr = ''

                    element = '<%s%s>' % (name, attr)
                    element += '<title>%s</title>' % title
                    logger.debug(' ' + element)

                    argIndex = 1
                    for part in parts:
                        if 'eqpos' in part:
                            argName = part.out[0:part.eqpos]
                            argValue = part.out[part.eqpos + 1:]
                            element += '<part><name>%s</name>=' % argName \
                                + '<value>%s</value></part>' % argValue
                        else:
                            element += '<part><name index="%s" />' % argIndex \
                                + '<value>%s</value></part>' % part.out
                            argIndex += 1
                    element += '</%s>' % name

                # Advance input pointer
                i += matchingCount

                # Unwind the stack
                stack.pop()

                # Re-add the old stack element if it still has unmatched
                # opening characters remaining
                if matchingCount < piece.data['count']:
                    piece.parts = [PPDPart()]
                    piece.data['count'] -= matchingCount
                    # do we still qualify for any callback with remaining cnt?
                    omin = rules[piece.data['open']]['min']
                    if piece.data['count'] >= omin:
                        stack.append(piece)
                    else:
                        stack.accum += piece.data['open'] * piece.data['count']

                flags = stack.getFlags()
                findPipe = flags['findPipe']
                findEquals = flags['findEquals']

                # Add XML element to the enclosing accumulator
                stack.accum += element

            elif found == 'pipe':
                findEquals = True    # shortcut for getFlags()
                stack.addPart()
                i += 1
            elif found == 'equals':
                findEquals = False   # shortcut for getFlags()
                stack.getCurrentPart().eqpos = len(stack.accum)
                stack.accum += '='
                i += 1

    # Output any remaining unclosed brackets
    for piece in stack.stack:
        logger.debug('Adding stack element with unclosed brackets')
        stack.rootAccum += piece.breakSyntax()

    stack.rootAccum += '</root>'
    xml = stack.rootAccum

    #print accum
    return xml

#xml = preprocessToXml('LLorem ipsum {{{{{Min lille mal}}} | Kake = sake }}')
#print xml
