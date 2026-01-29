#!/usr/bin/env python3

# requires:
#  sudo apt install python3-png

# dump original font:
#  ./dump.py --rom loretta.sg --font original/font.txt
#  ./dump.py --rom loretta.sg --font original/font.png --png

# dump original text:
#  ./dump.py --rom loretta.sg --text original/text.txt --charmap original/font.txt
#  ./dump.py --rom loretta.sg --menu original/menu.txt --charmap original/font.txt
#  ./dump.py --rom loretta.sg --words original/words.txt --charmap original/font.txt


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
    [strings, num_bytes] = charmap.get_strings(rom, 0x1C000, 0x17B)
    pointers = {}

    ptr_offset = 0x14000
    start_scan = 0x35C0
    end_scan = 0x79FF
    for address in strings.keys():
        if (len(pointers) < 4):
            ptr = rom.find_value(address - ptr_offset, 0x2500, 0x25FF)
        else:
            ptr = rom.find_value(address - ptr_offset, start_scan, end_scan)
            if ptr != 0 and ptr < start_scan + 0x20:
                start_scan = ptr + 8

        if ptr != 0:
            pointers[address] = [ptr]

    charmap.dump(rom, 0x1C000, num_bytes, options.text_path, strings, pointers, -ptr_offset)

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
