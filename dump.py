#!/usr/bin/env python3

# requires:
#  sudo apt install python3-png

# dump original font:
#  ./dump.py --rom loretta.sg --font original/font.txt --count 0x92
#  ./dump.py --rom loretta.sg --font original/font.png --count 0x92 --png

# dump original text:
#  ./dump.py --rom loretta.sg --text original/title_text.txt --charmap original/font.txt --address 0x2B35 --count 4
#  ./dump.py --rom loretta.sg --text original/menu.txt --charmap original/font.txt --address 0x200F --count 14
#  ./dump.py --rom loretta.sg --text original/time.txt --charmap original/font.txt --address 0x2C0E --count 1
#  ./dump.py --rom loretta.sg --text original/words.txt --charmap original/font.txt --address 0x2119 --count 91
#  ./dump.py --rom loretta.sg --text original/text.txt --charmap original/font.txt --address 0x1C000 --count 0x17B


from utils.rom import ROM
from utils.tiles import TileTable, Format
from utils.charmap import CharMap
from utils.strings import StringTable

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
parser.add_option('-a', '--address', action='store', dest='address', help='address to read from')
parser.add_option('-n', '--count', action='store', default='256', dest='count', help='number of tiles or strings to read')


options, args = parser.parse_args()

if not options.rom_path:
    print("--rom is required")
    exit()

if not os.path.isfile(options.rom_path):
    print(options.rom_path + " not found")
    exit()

if not options.address:
    print("--address is required")
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

    address = int(options.address, 0)
    count = int(options.count, 0)

    charmap = CharMap(options.charmap_path)
    [strings, num_bytes] = charmap.get_strings(rom, address, count)
    pointers = {}
    ptr_offset = 0

    if address == 0x1C000:
        # attempt to identify the pointers for the dialog text strings
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

    StringTable.dump(options.text_path, strings, num_bytes, address, pointers, -ptr_offset)
