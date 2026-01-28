#!/usr/bin/env python3

# import font:
#  ./import.py --rom loretta_en.sg --font english_font.txt

# import text:
#  ./import.py --rom loretta_en.sg --text english_text.txt --charmap english_font.txt
#  ./import.py --rom loretta_en.sg --menu english_menu.txt --charmap english_font.txt
#  ./import.py --rom loretta_en.sg --words english_words.txt --charmap english_font.txt

from utils.rom import ROM
from utils.tiles import TileTable, Format
from utils.charmap import CharMap

import optparse
import os

parser = optparse.OptionParser()
parser.add_option('-r', '--rom', action='store', dest='rom_path', help='source ROM to dump from')
parser.add_option('-s', '--font', action='store', dest='font_path', help='import font from file')
parser.add_option('-t', '--text', action='store', dest='text_path', help='import strings to file')
parser.add_option('-m', '--menu', action='store', dest='menu_path', help='import menu strings to file')
parser.add_option('-w', '--words', action='store', dest='word_path', help='import word strings to file')
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

# if options.text_path:
#     if not options.charmap_path:
#         printf("--charmap is required for --text")
#         exit()

#     charmap = CharMap(options.charmap_path)
#     charmap.dump(rom, 0x1C000, 0x17B, options.text_path)

if options.menu_path:
    if not options.charmap_path:
        printf("--charmap is required for --menu")
        exit()

    charmap = CharMap(options.charmap_path)
    charmap.import_from_text(rom, 0x200F, 0x3C, options.menu_path)

if options.word_path:
    if not options.charmap_path:
        printf("--charmap is required for --menu")
        exit()

    charmap = CharMap(options.charmap_path)
    charmap.import_from_text(rom, 0x2119, 0x265, options.word_path)

rom.commit()
