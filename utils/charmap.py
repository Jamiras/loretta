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
                value_start = line.find('@"')
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

                        value = line[value_start:value_end].replace('\\n', '\n')
                        self.map[key] = value

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


    def dump(self, rom, address, count, filename, pointers = {}):
        start = address
        i = 0
        with open(filename, 'w', encoding='utf-8') as file:
            if address in pointers:
                for pointer in pointers[address]:
                    file.write('@{0:04X}\n'.format(pointer))
            file.write('${0:04X}|'.format(i))

            ends_with_space = False
            b1 = rom.get_byte(address)
            while count > 0:
                b2 = rom.get_byte(address + 1)
                b = (b1 << 8) | b2 | 0x10000
                address += 1
                
                if b in self.map:
                    file.write(self.map[b])
                    if len(self.map[b]) > 0:
                        ends_with_space = (self.map[b][-1] == ' ')

                    # consume both characters
                    address += 1
                    b2 = rom.get_byte(address)
                elif b1 in self.map:
                    b = b1
                    file.write(self.map[b])
                    if len(self.map[b]) > 0:
                        ends_with_space = (self.map[b1][-1] == ' ')
                else:
                    b = b1
                    file.write('[{0:02X}]'.format(b))
                    ends_with_space = False
                    
                if b in self.terminal:
                    if ends_with_space:
                        file.write('|')
                        ends_with_space = False
                        
                    file.write('\n')
                    count = count - 1
                    if count > 0:
                        i = i + 1
                        if address in pointers:
                            for pointer in pointers[address]:
                                file.write('@{0:04X}\n'.format(pointer))

                        file.write('${0:04X}|'.format(i))

                b1 = b2

        print('Dumped {0} bytes starting at ${1:04X}'.format(address - start, start))

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
                    l = key.len

            if l == 0:
                c = text[i]
                if c not in self.charmap:
                    print("no encoding for \"" + c + "\"")
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

    def import_from_text(self, rom, address, space, filename):
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
                    if text in strings:
                        pointer_text[text] += next_pointers
                        shared_strings += 1
                        encoded = strings[text]
                        shared_string_bytes += len(encoded)
                        total_bytes += len(encoded)
                    else:
                        encoded = self.encode(text)
                        strings[text] = encoded
                        total_bytes += len(encoded)
                        pointer_text[text] = next_pointers

                    next_pointers = []
                    num_strings += 1

                elif line.startswith('@'):
                    i = 1
                    while i < len(line) and line[i].isalnum():
                        i += 1
                    ptr = int(line[1:i], 16)
                    next_pointers.append(ptr)

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
                    pointers[ptr] = text_address

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
                    pointers[ptr] = text_address

            if len(pointers) > 0:
                print('Writing {0} pointers'.format(len(pointers)))
                for key, value in pointers.items():
                    rom.set_byte(key, value & 0xFF)
                    rom.set_byte(key + 1, value >> 8)
        else:
            print('Cannot write {0} bytes to ${1:02X} (exceeds {2} available space)'.format(len(bytes), address, space))

