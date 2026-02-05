from pathlib import Path
from utils.strings import Parser

# file format is a comment line marking the start of a character and it's hex value followed by 8 lines of pixel data
# pixel data is ignored by this class
#
# within a comment, a $ indicates the start of the hex value, and the text value is wrapped in a quoted @ string
# additonal text in the comment is ignored
#
# $40 @"0" zero
# ..####..
# .#....#.
# .#....#.
# .#....#.
# .#....#.
# .#....#.
# .#....#.
# ..####..

class CharMap:
    def __init__(self, filename):
        self.map = {}
        self.charmap = {}
        self.wordmap = {}
        self.terminal = []
        self.address = 0
        self.space = 256 * 8

        parser = Parser(filename)
        [line, line_index] = parser.readline()
        while line:
            # character mapping: $bytes @"match" @"secondarymatch" !"output" ignored
            # if !"output" is not present, the first @"match" is used for output
            # @"secondarymatch" is optional. additional matches may be provided
            # everything else is ignored when reading the file as a CharMap
            if line.startswith('$'):
                if len(line) > 3 and line[3].isalnum():
                    if len(line) > 5 and line[5].isalnum():
                        key = int(line[1:7], 16) | 0x2000000
                    else:
                        key = int(line[1:5], 16) | 0x1000000
                else:
                    key = int(line[1:3], 16)

                # explicit output text specified, capture it
                index = line.find(' !"')
                if index != -1:
                    [text, l] = Parser.parsequoted(line, index + 2)
                    self.map[key] = text

                # capture all the input texts. if an explicit output text was not
                # specified, the first input text will be used for output
                index = line.find('@"')
                while index != -1:
                    [text, l] = Parser.parsequoted(line, index + 1)
                    if key not in self.map:
                        self.map[key] = text
                    
                    if len(text) == 1:
                        self.charmap[text] = key
                    else:
                        self.wordmap[text] = key

                    index = line.find('@"', index + l + 2)

                # if the character is decorated as a terminator, capture it
                if '@terminal' in line:
                    self.terminal.append(key)
                
            [line, line_index] = parser.readline()

    def get_text(self, key):
        if key in self.map:
            return self.map[key]

        return '[{0:02X}]'.format(key)

    def is_terminal(self, key):
        return key in self.terminal

    def get_strings(self, rom, address, count):
        original_address = address
        strings = {}
        start = address
        s = ''

        while count > 0:
            b1 = rom.get_byte(address)
            b2 = rom.get_byte(address + 1)
            b3 = rom.get_byte(address + 2)
            bw = (b1 << 8) | b2 | 0x1000000
            bt = (b1 << 16) | (b2 << 8) | b3 | 0x2000000
            address += 1
            
            if bt in self.map:
                b = bt
                address += 2 # consume three bytes
            elif bw in self.map:
                b = bw
                address += 1 # consume two bytes
            elif b1 in self.map:
                b = b1
            else:
                s += '[{0:02X}]'.format(b1)
                b = None
                
            if b is not None:
                s += self.map[b]

                if b in self.terminal:
                    strings[start] = s
                    start = address
                    s = ''

                    count = count - 1

        if s != '':
            strings[start] = s

        print('Read {0} bytes starting at ${1:04X}'.format(address - original_address, original_address))
        return [strings, address - original_address]

    def encode_match(self, text, index):
        c = None
        l = 0
        for key, value in self.wordmap.items():
            if len(key) > l and text.startswith(key, index):
                return [value, len(key)]

        c = text[index]
        if c not in self.charmap:
            #print("no encoding for \"" + c + "\"")
            return [0, 0]

        return [self.charmap[c], 1]

    @staticmethod
    def __encode_append(encoded, c):
        if c >= 0x2000000:
            encoded.append((c >> 16) & 0xFF)
        if c >= 0x1000000:
            encoded.append((c >> 8) & 0xFF)
        encoded.append(c & 0xFF)

    def encode(self, text):
        encoded = bytearray()
        i = 0
        c = None
        while i < len(text):
            [c, l] = self.encode_match(text, i)

            if l > 0:
                CharMap.__encode_append(encoded, c)
                i += l

        if c not in self.terminal:
            c = self.terminal[0]
            CharMap.__encode_append(encoded, c)

        return encoded
