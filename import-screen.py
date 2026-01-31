#!/usr/bin/env python3

# import title:
#  ./import-screen.py --rom loretta_en.sg --screen english/title.png --address 0x1A128 --tileaddress 0x19F8B --tilespace 0x1D8

from utils.rom import ROM
from utils.screen import Screen
from utils.tiles import Format

import optparse
import os

parser = optparse.OptionParser()
parser.add_option('-r', '--rom', action='store', dest='rom_path', help='source ROM to dump from')
parser.add_option('-s', '--screen', action='store', dest='screen', help='png file to import')
parser.add_option('-a', '--address', action='store', dest='screen_address', help='address of screen data')
parser.add_option('-t', '--tileaddress', action='store', dest='tile_address', help='address of tile data')
parser.add_option('-c', '--tilespace', action='store', default='256', dest='tile_space', help='maximum space for tiles')

options, args = parser.parse_args()

if not options.rom_path:
    print("--rom is required")
    exit()

if not os.path.isfile(options.rom_path):
    print(options.rom_path + " not found")
    exit()

if not options.screen:
    print("--screen is required")
    exit()

rom = ROM(options.rom_path)

screen_address = int(options.screen_address, 0)
tile_address = int(options.tile_address, 0)
tile_space = int(options.tile_space, 0)

screen = Screen()
screen.import_image(rom, options.screen, Format.RLE_8x8_1BPP, screen_address, tile_address, tile_space)

rom.commit()
