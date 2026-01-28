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
    def tile_data(rom, address, format):
        size = TileTable.tile_size(format)
        tiledata = rom.get_bytes(address, size * 256)

        if format == Format.RLE_8x8_1BPP:
            tiledata = TileTable.__decode_rle(tiledata)

        return tiledata

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
    def __dump_ascii_art(file, tile, width, height, bpp):
        arts = {
            1: ['.', '#'],
            2: ['.', '-', '+', '#']
        }
        art = arts[bpp]
        
        i = 0
        for y in range(0, height):
            for x in range(0, width):
                file.write(art[tile[i]])
                i = i + 1
            file.write('\n')
    

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
