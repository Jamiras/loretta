#!/usr/bin/env python3

# import font:
#  ./import.py --rom loretta_en.sg --font english/font.txt

# import text:
#  ./import.py --rom loretta_en.sg --text english/text.txt --charmap english/font.txt
#  ./import.py --rom loretta_en.sg --text english/menu.txt --charmap english/font.txt
#  ./import.py --rom loretta_en.sg --text english/words.txt --charmap english/font.txt

from utils.rom import ROM
from utils.tiles import TileTable, Format
from utils.charmap import CharMap

import optparse
import os

parser = optparse.OptionParser()
parser.add_option('-r', '--rom', action='store', dest='rom_path', help='source ROM to dump from')
parser.add_option('-f', '--font', action='store', dest='font_path', help='import font from file')
parser.add_option('-t', '--text', action='store', dest='text_path', help='import strings to file')
parser.add_option('-c', '--charmap', action='store', dest='charmap_path', help='character map to use when importing strings')


options, args = parser.parse_args()

if not options.rom_path:
    print("--rom is required")
    exit()

if not os.path.isfile(options.rom_path):
    print(options.rom_path + " not found")
    exit()

rom = ROM(options.rom_path)

if options.font_path:
    TileTable.import_from_text(rom, 0x008000, Format.RLE_8x8_1BPP, options.font_path, space=0x717)

if options.text_path:
    if not options.charmap_path:
        print("--charmap is required for --text")
        exit()

    charmap = CharMap(options.charmap_path)
    charmap.import_from_text(rom, options.text_path)

rom.commit()
