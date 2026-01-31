from enum import Enum, unique
from utils.strings import Parser
from utils.tiles import TileTable

import png

class Screen:
    def __init__(self):
        self.tiles = []
        self.bpp = 1

    def readtiles(self, filename, bpp):
        tile_lines = []
        self.bpp = bpp
        art = TileTable.get_ascii_art(self.bpp)

        address = 0
        space = bpp * 256 * 8

        parser = Parser(filename)
        [line, line_index] = parser.readline()
        while line:
            if line[0] in art:
                if len(line) < 8:
                    print('Line {0} incomplete: {1}'.format(line_index, line))
                    line += "........"

                tile_lines.append(line[0:8])
                if len(tile_lines) == 8:
                    self.tiles.append(tile_lines)
                    tile_lines = []

            [line, line_index] = parser.readline()

    def dump_to_png(self, filename, rom, address, width, height):
        data = rom.get_bytes(address, width * height)
        art = TileTable.get_ascii_art(self.bpp)
        image = []

        offset = 0
        for y in range(0, height):
            row = [[], [], [], [], [], [], [], []]
            for x in range(0, width):
                tile = self.tiles[data[offset + x]]

                for y2 in range(0, 8):
                    line = tile[y2]
                    for x2 in range(0, 8):                                
                        try:
                            b = art.index(line[x2])
                        except ValueError:
                            print("unknown character \"" + line[x] + "\" in glyph: " + line)
                            b = 0

                        row[y2].append(b)

            image.append(row[0])
            image.append(row[1])
            image.append(row[2])
            image.append(row[3])
            image.append(row[4])
            image.append(row[5])
            image.append(row[6])
            image.append(row[7])
            offset += width

        file = open(filename, 'wb')
        w = png.Writer(width*8, height*8, greyscale=True, bitdepth=self.bpp)
        w.write(file, image)
        file.close()

    def import_image(self, rom, filename, format, address, tile_address, tile_space):
        file = png.Reader(filename=filename)
        stride, height, pixels, metadata = file.read_flat()

        tiles = {}
        screendata = []

        width = stride // 8
        height //= 8
        offset = 0
        for y in range(0, height):
            for x in range(0, width):
                tile = 0
                offset2 = offset + x * 8
                for y2 in range(0, 8):
                    for x2 in range(0, 8):
                        tile <<= 1
                        if pixels[offset2 + x2] != 0:
                            tile |= 1
                    offset2 += stride
                
                if tile in tiles:
                    screendata.append(tiles[tile])
                else:
                    i = len(tiles)
                    screendata.append(i)
                    tiles[tile] = i

            offset += stride * 8

        [screendata, tiles] = Screen.__optimize_for_rle(screendata, tiles)

        tiledata = []
        for tile in tiles:
            m = 56
            for i in range(0,8):
                tiledata.append((tile >> m) & 0xFF)
                m -= 8

        print('Generated {0} tiles'.format(len(tiles)))
        TileTable.write_tiles(tiledata, rom, tile_address, format, tile_space)

        rom.set_bytes(address, screendata)
        print('Wrote {0} bytes screen data to @{1:02X}'.format(len(screendata), address))

    @staticmethod
    def __optimize_for_rle(screendata, tiles):
        new_tiles = []

        tile_strings = {}
        for tile, i in tiles.items():
            tile_string = '{0:016X}'.format(tile)
            if i == 0:
                match = tile_string[-2:]
                new_tiles.append(tile)
            else:
                tile_strings[tile_string] = i

        # 0 must be the empty tile
        remap = {}
        remap[0] = 0

        while len(tile_strings) > 0:
            best = None
            best_len = 0
            last = None
            for tile_string in tile_strings.keys():
                if tile_string.startswith(match):
                    l = 2
                    while l < 16 and tile_string[l:l+2] == match:
                        l += 2

                    if l > best_len:
                        best_len = l
                        best = tile_string

                else:
                    last = tile_string

            if best is None:
                best = last

            old_id = tile_strings[best]
            new_id = len(new_tiles)
            for tile, i in tiles.items():
                if i == old_id:
                    new_tiles.append(tile)
                    break
            remap[old_id] = new_id
            del tile_strings[best]
            
            match = best[-2:]

        new_screendata = []
        for i in screendata:
            new_screendata.append(remap[i])

        return [new_screendata, new_tiles]    
