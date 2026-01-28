#!/usr/bin/env python3

# requires:
#  sudo apt install python3-png

# dump original font:
#  ./dump.py --rom loretta.sg --font original_font.txt
#  ./dump.py --rom loretta.sg --font original_font.png --png

# dump original text:
#  ./dump.py --rom loretta.sg --text original_text.txt --charmap original_font.txt
#  ./dump.py --rom loretta.sg --menu original_menu.txt --charmap original_font.txt
#  ./dump.py --rom loretta.sg --words original_words.txt --charmap original_font.txt


from utils.rom import ROM
from utils.tiles import TileTable, Format
from utils.charmap import CharMap

import optparse
import os

parser = optparse.OptionParser()
parser.add_option('-r', '--rom', action='store', dest='rom_path', help='source ROM to dump from')
parser.add_option('-s', '--font', action='store', dest='font_path', help='dump font to file')
parser.add_option('-p', '--png', action='store_true', default='False', dest='png', help='dump to PNG file instead of text')
parser.add_option('-t', '--text', action='store', dest='text_path', help='dump strings to file')
parser.add_option('-m', '--menu', action='store', dest='menu_path', help='dump menu strings to file')
parser.add_option('-w', '--words', action='store', dest='word_path', help='dump word strings to file')
parser.add_option('-c', '--charmap', action='store', dest='charmap_path', help='character map to use when dumping strings')


options, args = parser.parse_args()

if not options.rom_path:
    print("--rom is required")
    exit()

if not os.path.isfile(options.rom_path):
    print(options.rom_path + " not found")
    exit()

rom = ROM(options.rom_path)

if options.font_path:
    if options.png == True:
        TileTable.dump_to_png(rom, 0x008000, Format.RLE_8x8_1BPP, options.font_path)
    else:
        TileTable.dump_to_text(rom, 0x008000, Format.RLE_8x8_1BPP, options.font_path)

if options.text_path:
    if not options.charmap_path:
        printf("--charmap is required for --text")
        exit()

    charmap = CharMap(options.charmap_path)
    charmap.dump(rom, 0x1C000, 0x17B, options.text_path)

if options.menu_path:
    if not options.charmap_path:
        printf("--charmap is required for --menu")
        exit()

    charmap = CharMap(options.charmap_path)
    charmap.dump(rom, 0x200F, 0x0E, options.menu_path)

if options.word_path:
    if not options.charmap_path:
        printf("--charmap is required for --menu")
        exit()

    charmap = CharMap(options.charmap_path)
    charmap.dump(rom, 0x2119, 0x5B, options.word_path, pointers=rom.get_pointers(0x204B, 0x67))
