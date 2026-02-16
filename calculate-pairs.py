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
table.share_pointers()

match_length = 2
sequences = {}
for text in table.strings:
    if not text:
        continue
    
    for clause in text.split('[WAIT]'):
        clause = clause.replace('[NL]', '\n')
        for i in range(0, len(clause) - match_length):
            sequence = clause[i:i+match_length]

            if sequence not in sequences:
                sequences[sequence] = 1
            else:
                sequences[sequence] += 1

long_sequences = {}
for sequence, count in sequences.items():
    if count > 2:
        long_sequences[sequence] = count

weighted_sequences = dict(sorted(long_sequences.items(), key=lambda item: item[1], reverse=True))

i = 0xA0
with open(options.output_path, "w") as file:
    for sequence, c in weighted_sequences.items():
        sequence = sequence.replace('\n', '[NL]')
        file.write('${0:02X} @"{1}"\n'.format(i, sequence))

        i += 1
        if i == 0xFE:
            break

print("Wrote words to " + options.output_path)
