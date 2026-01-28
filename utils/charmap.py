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
                        
                        if '@terminal' in line:
                            self.terminal.append(key)
                
                line = file.readline()

    def get_text(self, key):
        if key in self.map:
            return self.map[key]

        return '[{0:02X}]'.format(key)

    def is_terminal(self, key):
        return key in self.terminal

    def dump(self, rom, address, count, filename):
        i = 0
        with open(filename, 'w', encoding='utf-8') as file:
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
                        file.write('${0:04X}|'.format(i))

                b1 = b2
