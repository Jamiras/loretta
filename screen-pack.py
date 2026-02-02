#!/usr/bin/env python3

# import title:
#  ./screen-pack.py --rom loretta_en.sg

from utils.rom import ROM
from utils.terminal import Color

import optparse
import os

parser = optparse.OptionParser()
parser.add_option('-r', '--rom', action='store', dest='rom_path', help='source ROM to dump from')

options, args = parser.parse_args()

if not options.rom_path:
    print("--rom is required")
    exit()

if not os.path.isfile(options.rom_path):
    print(options.rom_path + " not found")
    exit()

rom = ROM(options.rom_path)

num_screens = 30
screen_address_base = 0x67E7
screen_address = {}
screen_addresses = []
for i in range(0, num_screens):
    screen_address[i] = rom.get_byte(screen_address_base + i * 2) | (rom.get_byte(screen_address_base + i * 2 + 1) << 8)
    if screen_address[i] not in screen_addresses:
        screen_addresses.append(screen_address[i])

leads = {}
trails = {}
screens = {}
for address in screen_addresses:
    if address != 0:
        screen = rom.get_bytes(address + 0x14000, 11*16)
        screens[address] = screen
        
        j = 0
        while screen[j] == 0:
            j += 1
        leads[address] = j

        j = 0
        while screen[-(j+1)] == 0:
            j += 1
        trails[address] = j

offsets = {}
data = bytearray()

best_joins = {}
remaining_trails = dict(trails)
remaining_leads = dict(leads)
while len(remaining_trails) > 1:
    longest_trail = -1
    longest_trail_address = -1
    for address, trail in remaining_trails.items():
        if trail > longest_trail:
            longest_trail = trail
            longest_trail_address = address
    del remaining_trails[longest_trail_address]

    longest_lead = -1
    longest_lead_address = -1
    for address, lead in remaining_leads.items():
        if lead > longest_lead:
            is_cycle = False
            cycle_address = address
            while not is_cycle:
                if cycle_address not in best_joins:
                    break
                cycle_address = best_joins[cycle_address]
                if cycle_address == longest_trail_address:
                    is_cycle = True

            if not is_cycle:
                longest_lead = lead
                longest_lead_address = address
        
    del remaining_leads[longest_lead_address]

    best_joins[longest_trail_address] = longest_lead_address
    #print('{0:02X}=>{1:02X}:{2}>{3}'.format(longest_trail_address, longest_lead_address, longest_trail, longest_lead))

next_address = 0
for address in remaining_leads.keys():
    next_address = address

prev_trail = 0
while next_address != 0:
    shared = min(prev_trail, leads[next_address])
    offsets[next_address] = len(data) - shared
    data.extend(screens[next_address][shared:])
    #print('{0:02X} {1} {2}|<{3} {4}>|{5}'.format(next_address, shared, prev_trail, leads[next_address], trails[next_address], len(data)))

    prev_trail = trails[next_address]
    next_address = 0 if next_address not in best_joins else best_joins[next_address]

print('Saved {0} bytes by overlapping screen interaction data'.format(11*16*len(screens) - len(data)))

base_address = 0x20000 - len(data)
rom.set_bytes(base_address, data)
print(Color.OKGREEN + 'Wrote {0} bytes to ${1:02X}'.format(len(data), base_address) + Color.RESET)

for i in range(0, num_screens):
    if screen_address[i] != 0:
        address = base_address - 0x14000 + offsets[screen_address[i]]
        #print('{0:02X}=>{1:02X}'.format(screen_address[i], address))
        rom.set_byte(screen_address_base + i * 2, address & 0xFF)
        rom.set_byte(screen_address_base + i * 2 + 1, address >> 8)

rom.commit()
