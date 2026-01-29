from pathlib import Path

# file format is a comment line marking the start of a character and it's hex value followed by 8 lines of pixel data
# pixel data is ignored by this class
#
# within a comment, a $ indicates the start of the hex value, and the text value is wrapped in a quoted @ string
# additonal text in the comment is ignored
#
# // $40 @"0" zero
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
        
        line_index = 0
        with open(filename, 'r', encoding='utf-8') as file:
            line = file.readline()

            while line:
                line_index += 1
                value_start = line.find('@"') # dump/import text
                if value_start == -1:
                    value_start = line.find('!"') # dump only text

                if value_start >= 0:
                    key_start = line.find('$')
                    if key_start >= 0:
                        if line[key_start + 3].isalnum():
                            key = int(line[key_start+1:key_start+5], 16) | 0x10000
                        else:
                            key = int(line[key_start+1:key_start+3], 16)

                        value_start += 2
                        value_end = value_start
                        line_len = len(line)
                        while value_end < line_len and line[value_end] != '"':
                            if line[value_end] == '\\' and line[value_end + 1] != 'n':
                                value_end += 2
                            else:
                                value_end += 1

                        if value_end >= line_len:
                            print("Unterminated string on line " + str(line_index))
                        
                        value = line[value_start:value_end]
                        if value.find('\\') != -1:
                            value = value.replace('\\n', '\n').replace('\\', '')
                        self.map[key] = value

                        if line[value_start - 2] == '@':
                            if len(value) == 1:
                                self.charmap[value] = key
                            else:
                                self.wordmap[value] = key
                        
                        if '@terminal' in line:
                            self.terminal.append(key)
                
                line = file.readline()

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

        b1 = rom.get_byte(address)
        while count > 0:
            b2 = rom.get_byte(address + 1)
            b = (b1 << 8) | b2 | 0x10000
            address += 1
            
            if b in self.map:
                s += self.map[b]

                # consume both characters
                address += 1
                b2 = rom.get_byte(address)
            elif b1 in self.map:
                b = b1
                s += self.map[b]
            else:
                b = b1
                s += '[{0:02X}]'.format(b)
                
            if b in self.terminal:
                strings[start] = s
                start = address
                s = ''

                count = count - 1

            b1 = b2

        print('Read {0} bytes starting at ${1:04X}'.format(address - original_address, original_address))
        return [strings, address - original_address]

    def dump(self, rom, address, count, filename, strings = None, pointers = {}, ptr_offset = 0):
        if not strings:
            [strings, count] = self.get_strings(rom, address, count)

        i = 0
        with open(filename, 'w', encoding='utf-8') as file:
            file.write('|${0:04X} address\n'.format(address))
            file.write('|#{0:04X} bytes\n'.format(count))
            if ptr_offset > 0:
                file.write('|+{0:04X} pointer offset\n'.format(ptr_offset))
            elif ptr_offset < 0:
                file.write('|{0:04X} pointer offset\n'.format(ptr_offset))
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

    def encode(self, text):
        encoded = bytearray()
        i = 0
        c = None
        while i < len(text):
            c = None
            l = 0
            for key, value in self.wordmap.items():
                if len(key) > l and text.startswith(key, i):
                    c = value
                    l = len(key)

            if l == 0:
                c = text[i]
                if c not in self.charmap:
                    #print("no encoding for \"" + c + "\"")
                    break
                else:
                    c = self.charmap[c]
                    l = 1

            if l > 0:
                if c >= 0x10000:
                    encoded.append((c >> 8) & 0xFF)
                    encoded.append(c & 0xFF)
                else:
                    encoded.append(c)

            i += l

        if c not in self.terminal:
            c = self.terminal[0]
            if c >= 0x10000:
                encoded.append((c >> 8) & 0xFF)
                encoded.append(c & 0xFF)
            else:
                encoded.append(c)

        return encoded

    @staticmethod
    def __apply_wrap(text, wrap):
        wrapped_text = ''
        while len(text) > wrap:
            index = text.rfind(' ', 0, wrap + 1)
            if index == -1:
                index = text.find(' ', wrap)
                if index == -1:
                    break
            wrapped_text += text[0:index]
            wrapped_text += '\n'
            text = text[index + 1:]

        wrapped_text += text
        return wrapped_text

    @staticmethod
    def __read_hex(line, index):
        start = index
        while index < len(line) and line[index].isalnum():
            index += 1
        if start == index:
            return 0
        return int(line[start:index], 16)

    def import_from_text(self, rom, filename):
        address = 0
        space = 0
        ptr_offset = 0
        wrap = 0x100000
        wrap_char = 0
        pointer_text = {}
        strings = {}

        num_strings = 0
        shared_strings = 0
        shared_string_bytes = 0
        total_bytes = 0
        next_pointers = []
        with open(filename, 'r', encoding='utf-8') as file:
            line = file.readline()

            while line:
                line = line.strip()
                if line.startswith('$'):
                    text = line[line.index('|') + 1:]
                    if '|' in text:
                        text = text[:text.index('|')]

                    if len(text) > wrap:
                        parts = text.split('[WAIT]')
                        text = ''
                        first = True
                        for part in parts:
                            if first:
                                first = False
                            else:
                                if part.startswith('^'):
                                    part = part[1:]
                                    text += '[WAIT]\n'
                                else:
                                    if text != '':
                                        text += '\n'
                                    text += '[WAIT]'
                            text += CharMap.__apply_wrap(part, wrap)

                    if text in strings:
                        pointer_text[text] += next_pointers
                        shared_strings += 1
                        encoded = strings[text]
                        shared_string_bytes += len(encoded)
                    else:
                        encoded = self.encode(text)
                        strings[text] = encoded
                        pointer_text[text] = next_pointers

                    total_bytes += len(encoded)
                    next_pointers = []
                    num_strings += 1

                elif line.startswith('@') and len(line) >= 5:
                    ptr = CharMap.__read_hex(line, 1)
                    next_pointers.append(ptr)

                elif line.startswith('!address $'):
                    address = CharMap.__read_hex(line, 10)

                elif line.startswith('!space '):
                    space = CharMap.__read_hex(line, 7)

                elif line.startswith('!pointeroffset '):
                    if line[15] == '+':
                        ptr_offset = CharMap.__read_hex(line, 16)
                    else:
                        ptr_offset = -CharMap.__read_hex(line, 16)

                elif line.startswith('!wrap '):
                    wrap = CharMap.__read_hex(line, 6)
                    index = line.find('$')
                    if index != -1:
                        self.charmap['\n'] = CharMap.__read_hex(line, index + 1)

                line = file.readline()

        print('Read {0} strings requiring {1} bytes'.format(num_strings, total_bytes))

        trailing_strings = {}
        for s, s_bytes in strings.items():
            bytes_len = len(s_bytes)
            for s2, s_bytes2 in strings.items():
                bytes2_len = len(s_bytes2)
                if bytes2_len > bytes_len and s_bytes2[bytes2_len - bytes_len:] == s_bytes:
                    trailing_strings[s] = s2

        text_addresses = {}
        pointers = {}
        bytes = bytearray()
        for s, s_bytes in strings.items():
            if s not in trailing_strings:
                text_address = address + len(bytes)
                text_addresses[s] = text_address
                for ptr in pointer_text[s]:
                    pointers[ptr] = text_address + ptr_offset

                bytes.extend(s_bytes)

        shared_strings += len(trailing_strings)
        if shared_strings > 0:
            for s in trailing_strings.keys():
                shared_string_bytes += len(strings[s])
            print('Found {0} strings that can be shared, saving {1} bytes'.format(shared_strings, shared_string_bytes))

        if len(bytes) <= space:
            print('Writing {0}/{1} bytes to ${2:02X}'.format(len(bytes), space, address))
            rom.set_bytes(address, bytes)

            for s, s2 in trailing_strings.items():
                s3 = s2
                while s3 in trailing_strings:
                    s3 = trailing_strings[s3]
                
                text_address = text_addresses[s3] + len(s3) - len(s)
                for ptr in pointer_text[s]:
                    pointers[ptr] = text_address + ptr_offset

            if len(pointers) > 0:
                print('Writing {0} pointers'.format(len(pointers)))
                for key, value in pointers.items():
                    rom.set_byte(key, value & 0xFF)
                    rom.set_byte(key + 1, value >> 8)
        else:
            print('Cannot write {0} bytes to ${1:02X} (exceeds {2} available space)'.format(len(bytes), address, space))

