from enum import Enum, unique
import png

@unique
class Format(Enum):
    PLANAR_8x8_1BPP = 1
    PLANAR_8x8_2BPP = 2
    INTERTWINED_8x8_2BPP = 3
    RLE_8x8_1BPP = 4
    
    @staticmethod
    def get_bpp(format):
        bpp = {
            Format.PLANAR_8x8_1BPP: 1,
            Format.PLANAR_8x8_2BPP: 2,
            Format.INTERTWINED_8x8_2BPP: 2,
            Format.RLE_8x8_1BPP: 1,
        }
        return bpp.get(format, "Invalid format")
    

class TileTable:
    @staticmethod
    def tile_size(format):
        return Format.get_bpp(format) * 8

            
    @staticmethod
    def __get_bits(byte):
        return bytes(((byte >> 7) & 1,
                      (byte >> 6) & 1,
                      (byte >> 5) & 1,
                      (byte >> 4) & 1,
                      (byte >> 3) & 1,
                      (byte >> 2) & 1,
                      (byte >> 1) & 1,
                      (byte >> 0) & 1))
            
    @staticmethod
    def __decode_planar_8x8_1bpp(encoded_bytes):
        tile = bytearray()
        for y in range(0, 8):
            plane0 = TileTable.__get_bits(encoded_bytes[y])
            tile.extend(plane0)
                
        tile_bytes = bytes(tile)
        return tile_bytes

    @staticmethod
    def __encode_planar_8x8_1bpp(encoded_bytes):
        tile = bytearray()
        offset = 0
        for y in range(0, 8):
            b = 0x80 if encoded_bytes[offset + 0] != 0 else 0
            b |= 0x40 if encoded_bytes[offset + 1] != 0 else 0
            b |= 0x20 if encoded_bytes[offset + 2] != 0 else 0
            b |= 0x10 if encoded_bytes[offset + 3] != 0 else 0
            b |= 0x08 if encoded_bytes[offset + 4] != 0 else 0
            b |= 0x04 if encoded_bytes[offset + 5] != 0 else 0
            b |= 0x02 if encoded_bytes[offset + 6] != 0 else 0
            b |= 0x01 if encoded_bytes[offset + 7] != 0 else 0
            tile.append(b)
            offset += 8
                
        tile_bytes = bytes(tile)
        return tile_bytes

    @staticmethod
    def __decode_planar_8x8_2bpp(encoded_bytes):
        tile = bytearray()
        for y in range(0, 8):
            plane0 = TileTable.__get_bits(encoded_bytes[y])
            plane1 = TileTable.__get_bits(encoded_bytes[y + 8])
            for x in range(0, 8):
                tile.append(plane0[x] | (plane1[x] << 1))
                
        tile_bytes = bytes(tile)
        return tile_bytes

    @staticmethod
    def __decode_intertwined_8x8_2bpp(encoded_bytes):
        tile = bytearray()
        for y in range(0, 8):
            plane0 = TileTable.__get_bits(encoded_bytes[y * 2])
            plane1 = TileTable.__get_bits(encoded_bytes[y * 2 + 1])
            for x in range(0, 8):
                tile.append(plane0[x] | (plane1[x] << 1))
                
        tile_bytes = bytes(tile)
        return tile_bytes

    @staticmethod
    def __decode_rle(encoded_bytes):
        decoded_bytes = bytearray()

        i = 0
        j = 0
        while (j < 256 * 8):
            count = encoded_bytes[i]
            i += 1
            if (count < 0x80):
                j += count
                c = encoded_bytes[i]
                i += 1
                while (count > 0):
                    decoded_bytes.append(c)
                    count -= 1
            else:
                count -= 0x80
                j += count
                while (count > 0):
                    c = encoded_bytes[i]
                    i += 1
                    decoded_bytes.append(c)
                    count -= 1

        return decoded_bytes

    @staticmethod
    def __encode_rle(decoded_bytes):
        encoded_bytes = bytearray()

        start = 0
        count = 0
        rle_count = 1
        c = -1
        i = 0
        while (i < len(decoded_bytes)):
            r = decoded_bytes[i]

            if r == c:
                rle_count += 1
            else:
                if rle_count > 3 or (rle_count == 3 and count > 4):
                    count -= rle_count

                    if count > 0:
                        encoded_bytes.append(count | 0x80)
                        while count > 0:
                            encoded_bytes.append(decoded_bytes[start])
                            start += 1
                            count -= 1

                    encoded_bytes.append(rle_count)
                    encoded_bytes.append(c)

                    start = i
                    count = 0

                c = r
                rle_count = 1

            count += 1
            i += 1

        if rle_count == 3 and count <= 4:
            rle_count = 1

        if rle_count > 2:
            count -= rle_count

        if count > 0:
            encoded_bytes.append(count | 0x80)
            while count > 0:
                encoded_bytes.append(decoded_bytes[start])
                start += 1
                count -= 1

        if rle_count > 2:
            encoded_bytes.append(rle_count)
            encoded_bytes.append(c)

        return encoded_bytes

    @staticmethod
    def tile_data(rom, address, format):
        size = TileTable.tile_size(format)
        tiledata = rom.get_bytes(address, size * 256)

        if format == Format.RLE_8x8_1BPP:
            tiledata = TileTable.__decode_rle(tiledata)

        return tiledata

    @staticmethod
    def write_tiles(bytes, rom, address, format, space):
        if format == Format.RLE_8x8_1BPP:
            bytes = TileTable.__encode_rle(bytes)

        if len(bytes) <= space:
            print('Writing {0}/{1} bytes to ${2:02X}'.format(len(bytes), space, address))
            rom.set_bytes(address, bytes)
        else:
            print('Cannot write {0} bytes to ${1:02X} (exceeds {2} available space)'.format(len(bytes), address, space))

    @staticmethod
    def decode(bytes, format):
        decoders = {
            Format.PLANAR_8x8_1BPP: TileTable.__decode_planar_8x8_1bpp,
            Format.PLANAR_8x8_2BPP: TileTable.__decode_planar_8x8_2bpp,
            Format.INTERTWINED_8x8_2BPP: TileTable.__decode_intertwined_8x8_2bpp, 
            Format.RLE_8x8_1BPP: TileTable.__decode_planar_8x8_1bpp,
        }
        func = decoders.get(format, "Invalid format")
        return func(bytes)

    @staticmethod
    def __get_ascii_art(bpp):
        arts = {
            1: ['.', '#'],
            2: ['.', '-', '+', '#']
        }
        return arts[bpp]

    @staticmethod
    def __dump_ascii_art(file, tile, width, height, bpp):
        art = TileTable.__get_ascii_art(bpp)
        
        i = 0
        for y in range(0, height):
            for x in range(0, width):
                file.write(art[tile[i]])
                i = i + 1
            file.write('\n')
        
    @staticmethod
    def encode(tile_lines, format):
        art = TileTable.__get_ascii_art(Format.get_bpp(format))
        bytes = bytearray()

        i = 0
        for y in range(0, 8):
            line = tile_lines[y]
            for x in range(0, 8):
                try:
                    b = art.index(line[x])
                except ValueError:
                    print("unknown character \"" + line[x] + "\" in glyph: " + line)
                    b = 0

                bytes.append(b)

        encoders = {
            Format.PLANAR_8x8_1BPP: TileTable.__encode_planar_8x8_1bpp,
            Format.RLE_8x8_1BPP: TileTable.__encode_planar_8x8_1bpp,
        }
        func = encoders.get(format, "Invalid format")
        return func(bytes)

    @staticmethod
    def dump_to_text(rom, address, format, filename):
        file = open(filename, 'w')
        size = TileTable.tile_size(format)
        tiledata = TileTable.tile_data(rom, address, format)

        offset = 0
        for i in range(0, 256):
            bytes = tiledata[offset:offset+size]
            tile = TileTable.decode(bytes, format)
            
            file.write('// ${0:02X} @"?"\n'.format(i))
            TileTable.__dump_ascii_art(file, tile, 8, 8, Format.get_bpp(format))
            file.write('\n')
            
            offset += size
            
        file.close()


    @staticmethod
    def dump_to_png(rom, address, format, filename):
        image = []
        size = TileTable.tile_size(format)
        tiledata = TileTable.tile_data(rom, address, format)

        offset = 0
        for y in range(0, 16):
            row = []
            for x in range(0, 16):
                bytes = tiledata[offset:offset+size]
                tile = TileTable.decode(bytes, format)
                row.append(tile)
                offset += size

            for line in range(0, 8):
                image_row = bytearray()
                for i in range(0, 16):
                     image_row.extend(row[i][line * 8:line * 8 + 8])
                image.append(image_row)

        file = open(filename, 'wb')
        w = png.Writer(16*8, 16*8, greyscale=True, bitdepth=Format.get_bpp(format))
        w.write(file, image)
        file.close()


    def import_from_text(rom, address, format, filename, space=None):
        tile_lines = []
        bytes = bytearray()

        if space == None:
            space = Format.get_bpp(format) * 256 * 8

        with open(filename, 'r', encoding='utf-8') as file:
            line = file.readline()

            i = 0
            while line:
                i += 1
                line = line.strip()
                if line != '' and not line.startswith("//"):
                    if len(line) < 8:
                        print ("Line " + str(i) + " incomplete: " + line)
                        line += "........"

                    tile_lines.append(line)
                    if len(tile_lines) == 8:
                        tile = TileTable.encode(tile_lines, format)
                        bytes.extend(tile)
                        tile_lines = []

                line = file.readline()

        TileTable.write_tiles(bytes, rom, address, format, space)




