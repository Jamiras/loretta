#!/usr/bin/env python3

#  ./calculate-pairs.py --text english/text.txt --charmap english/font.txt --out english/pairs.txt

from utils.rom import ROM
from utils.tiles import TileTable, Format
from utils.charmap import CharMap
from utils.strings import StringTable

import optparse
import os

parser = optparse.OptionParser()
parser.add_option('-t', '--text', action='store', dest='text_path', help='import strings to file')
parser.add_option('-c', '--charmap', action='store', dest='charmap_path', help='character map to use when importing strings')
parser.add_option('-o', '--out', action='store', dest='output_path', help='output file')


options, args = parser.parse_args()

if not options.text_path:
    print("--text is required")
    exit()

if not options.charmap_path:
    print("--charmap is required")
    exit()

if not options.output_path:
    print("--out is required")
    exit()

charmap = CharMap(options.charmap_path)
table = StringTable(options.text_path, charmap)

pairs = {}
for text in table.strings:
    for word in text.split('[WAIT]'):
        for i in range(0, len(word) - 1):
            pair = word[i:i+2]
            if '\n' not in pair:
                if pair not in pairs:
                    pairs[pair] = 1
                else:
                    pairs[pair] += 1

sorted_pairs = dict(sorted(pairs.items(), key=lambda item: item[1], reverse=True))

i = 0xA0
with open(options.output_path, "w") as file:
    for pair in sorted_pairs.keys():
        file.write('${0:2X} @"{1}"\n'.format(i, pair))
        i += 1
        if i == 0xFE:
            break

print("Wrote pairs to " + options.output_path)
