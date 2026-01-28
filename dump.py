#!/usr/bin/env python3

# requires:
#  sudo apt install python3-png

# dump original font:
#  ./dump.py --rom loretta.sg --font original_font.txt
#  ./dump.py --rom loretta.sg --font original_font.png --png

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
    charmap.dump(rom, 0x3B8703, 0x09A7, options.text_path)
