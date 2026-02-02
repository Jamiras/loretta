from pathlib import Path
from utils.terminal import Color

class Parser:
    def __init__(self, filename):
        self.line_index = 0
        self.file = open(filename, 'r', encoding='utf-8')

    def __del__(self):
        self.file.close()

    def readline(self):
        line = self.file.readline()
        while line:
            self.line_index += 1

            index = line.find('//')
            if index != -1:
                line = line[0:index]

            line = line.rstrip()
            if len(line) != 0:
                break

            line = self.file.readline()

        return [line, self.line_index]

    @staticmethod
    def parsehex(text, index = 0):
        start = index
        while index < len(text) and text[index].isalnum():
            index += 1

        if start == index:
            return 0

        return int(text[start:index], 16)

    @staticmethod
    def parsequoted(text, index = 0):
        if text[index] != '"':
            return [None, 0]

        index += 1
        start = index
        while index < len(text) and text[index] != '"':
            index += 2 if text[index] == '\\' else 1

        result = text[start:index]

        if index < len(text): # consume closing quote
            index += 1

        #returned length includes both quotes
        return [Parser.unescape(result), index - start + 1]

    @staticmethod
    def unescape(value):
        if value.find('\\') == -1:
            return value
    
        return value.replace('\\n', '\n').replace('\\', '')


class StringBlock:
    def __init__(self, address):
        self.address = address
        self.space = 0
        self.pointers = {}
        self.pointer_offset = 0
        self.encoded = {}
        self.written = False


class StringTable:
    def __init__(self, filename, charmap):
        self.charmap = charmap
        self.strings = []
        next_pointers = []
        self.blocks = []
        self.current_block = None
        self.extra_block = None
        self.wrap = 0x10000000
        self.wrap_break = {}
        self.pokes = {}
        self.trailing_strings = {}
        current_string = None
        num_strings = 0

        parser = Parser(filename)
        [line, line_index] = parser.readline()
        while line:
            # start of string: "$addr|text" or "$addr|text|ignored".
            # second pipe can also be used to prevent removal of trailing whitespace: "$addr|text  |"
            if line.startswith('$'):
                if current_string is not None:
                    self.__flush_current_string(current_string, next_pointers)
                    next_pointers = []
                    num_strings += 1
                
                current_string = line[line.index('|') + 1:]
                if '|' in current_string:
                    current_string = current_string[:current_string.index('|')]

            # string continued: "|moretext" or "|moretext|"
            elif line.startswith('|'):
                text = line[line.index('|') + 1]
                if '|' in text:
                    text = text[:text.index('|')]

                current_string += '\n'
                current_string += text

            # commands
            elif line.startswith('!'):
                if current_string is not None:
                    self.__flush_current_string(current_string, next_pointers)
                    current_string = None
                    next_pointers = []
                    num_strings += 1

                self.__process_command(line, line_index)

            # pointer: "@1234" will write the address of the next string at $1234
            elif line.startswith('@'):
                if current_string is not None:
                    self.__flush_current_string(current_string, next_pointers)
                    current_string = None
                    next_pointers = []
                    num_strings += 1

                address = Parser.parsehex(line, 1)
                next_pointers.append(address)

            # poke: "&addr=value" will write a single byte value at the specified address
            elif line.startswith('&'):
                parts = line.split('=')
                address = Parser.parsehex(parts[0], 1)
                value = Parser.parsehex(parts[1], 0)
                self.pokes[address] = value

            [line, line_index] = parser.readline()

        if current_string:
            self.__flush_current_string(current_string, next_pointers)
            num_strings += 1

        total_bytes = 0
        for block in self.blocks:
            for encoded in block.encoded.values():
                total_bytes += len(encoded)

        print('Read {0} strings requiring {1} bytes'.format(num_strings, total_bytes))

    def __flush_current_string(self, s, next_pointers):
        s = self.__apply_wrap(s)

        index = len(self.strings)
        self.strings.append(s)

        if len(next_pointers) > 0: 
            if index in self.current_block.pointers:
                self.current_block.pointers[index] += next_pointers
            else:
                self.current_block.pointers[index] = next_pointers

        encoded = self.charmap.encode(s)
        self.current_block.encoded[index] = encoded

    def __apply_wrap(self, text):
        original_text = text
        wrapped_text = ''

        line_start = 0
        line_len = 0
        potential_wrap = None
        i = 0
        while i < len(text):
            if line_len > 0:
                break_key = None
                for b in self.wrap_break:
                    if text.startswith(b, i) and (break_key is None or len(b) > len(break_key)):
                        break_key = b

                if break_key is not None:
                    wrapped_text += self.wrap_break[break_key]
                    potential_wrap = None
                    line_start = len(wrapped_text)
                    line_len = 0
                    i += len(break_key)
                    continue

            [c, l] = self.charmap.encode_match(text, i)
            if l == 0:
                i += 1
                continue

            line_len += (c >> 24) + 1
            if line_len > self.wrap and potential_wrap is not None:
                wrapped_text = wrapped_text[0:potential_wrap] + '\n' + wrapped_text[potential_wrap+1:]
                line_start = potential_wrap + 1
                line_len = len(wrapped_text) - line_start

            new_text = text[i:i+l]               
            i += l

            if new_text == ' ':
                potential_wrap = len(wrapped_text)

            wrapped_text += new_text

            if new_text == '\n' or new_text == '[NL]':
                line_start = len(wrapped_text)
                line_len = 0
                potential_wrap = None

        return wrapped_text

    def __process_command(self, line, line_index):
        if line.startswith('!address $'):
            address = Parser.parsehex(line, 10)
            self.current_block = StringBlock(address)
            self.blocks.append(self.current_block)

        elif line.startswith('!space '):
            space = Parser.parsehex(line, 7)
            self.current_block.space = space

        elif line.startswith('!pointeroffset '):
            if line[15] == '+':
                offset = Parser.parsehex(line, 16)
            else:
                offset = -Parser.parsehex(line, 16)
            self.current_block.pointer_offset = offset

        elif line.startswith('!wrap '):
            self.wrap = Parser.parsehex(line, 6)
            self.wrap_break = {}

        elif line.startswith('!wrapbreak '):
            index = line.find(' ', 11)
            needle = Parser.unescape(line[11:index])
            replacement = Parser.unescape(line[index+1:])

            index = replacement.find(' ')
            if index != -1:
                replacement = replacement[0:index]

            self.wrap_break[needle] = replacement

        elif line.startswith('!extraspace $'):
            address = Parser.parsehex(line, 13)
            space = Parser.parsehex(line, line.find(' ', 13) + 1)
            self.extra_block = StringBlock(address)
            self.extra_block.space = space
            self.blocks.append(self.extra_block)

        else:
            print(COLOR.WARNING + 'Unknown command (line {0}): {1}', line_index, line) + Color.RESET

    def share_pointers(self):
        self.trailing_strings = {}
        for b in self.blocks:
            for i, e in b.encoded.items():
                # can only share substring if pointed at
                if i in b.pointers:
                    el = len(e)
                    
                    for b2 in self.blocks:
                        for i2, e2 in b2.encoded.items():
                            e2l = len(e2)
                            if e2l > el and e2[e2l - el:] == e:
                                self.trailing_strings[i] = [i2, e2l - el]
                            elif e2l == el and i < i2 and e2 == e:
                                self.trailing_strings[i] = [i2, 0]

        strings_saved = 0
        bytes_saved = 0
        for i in self.trailing_strings.keys():
            encoded_len = 0
            for b in self.blocks:
                if i in b.encoded:
                    encoded_len = len(b.encoded[i])
                    bytes_saved += encoded_len
                    del b.encoded[i]

            self.strings[i] = None
            strings_saved += 1

        if strings_saved > 0:
            print('Found {0} strings that can be shared, saving {1} bytes'.format(strings_saved, bytes_saved))

    def update_rom(self, rom):
        string_addresses = {}

        for b in self.blocks:
            data = bytearray()
            address = b.address

            for i, e in b.encoded.items():
                if i not in string_addresses:
                    if self.extra_block and self.extra_block != b and len(data) + len(e) > b.space:
                        self.extra_block.encoded[i] = e
                    else:
                        string_addresses[i] = address
                        data.extend(e)
                        address += len(e)

            if len(data) <= b.space:
                rom.set_bytes(b.address, data)
                print(Color.OKGREEN + 'Wrote {0}/{1} bytes to ${2:02X}'.format(len(data), b.space, b.address) + Color.RESET)
                b.written = True
            else:
                print(Color.FAIL + 'Cannot write {0} bytes to ${1:02X} (exceeds {2} available space)'.format(len(data), b.address, b.space) + Color.RESET)

        pointer_count = 0
        for b in self.blocks:
            if b.written:
                for i, ptrs in b.pointers.items():
                    if i in self.trailing_strings:
                        i2, o = self.trailing_strings[i]
                        address = string_addresses[i2] + o
                    else:
                        address = string_addresses[i]

                    address += b.pointer_offset

                    for ptr in ptrs:
                        rom.set_byte(ptr, address & 0xFF)
                        rom.set_byte(ptr + 1, address >> 8)
                        pointer_count += 1

        if pointer_count > 0:
            print(Color.OKGREEN + 'Wrote {0} pointers'.format(pointer_count) + Color.RESET)

        if len(self.pokes) > 0:
            for address, value in self.pokes.items():
                rom.set_byte(address, value)
            print(Color.OKGREEN + 'Wrote {0} pokes'.format(len(self.pokes)) + Color.RESET)

    @staticmethod
    def dump(filename, strings, space, address, pointers = {}, ptr_offset = 0):
        i = 0
        with open(filename, 'w', encoding='utf-8') as file:
            file.write('!address ${0:04X}\n'.format(address))
            file.write('!space {0:04X}\n'.format(space))
            if ptr_offset > 0:
                file.write('!pointeroffset +{0:04X}\n'.format(ptr_offset))
            elif ptr_offset < 0:
                file.write('!pointeroffset {0:04X}\n'.format(ptr_offset))
            file.write('\n')

            for start, text in strings.items():
                if start in pointers:
                    for pointer in pointers[start]:
                        file.write('@{0:04X}\n'.format(pointer))

                if len(text) > 0 and text[-1].isspace():
                    file.write('${0:04X}|{1}|\n\n'.format(start, text))
                else:
                    file.write('${0:04X}|{1}\n\n'.format(start, text))

        print('Dumped {0} strings'.format(len(strings)))