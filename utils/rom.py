from pathlib import Path

class ROM:
    def __init__(self, filename):
        self.filename = filename       

        self.size = Path(filename).stat().st_size
               
        file = open(filename, "rb")
        self.data = bytearray(file.read(self.size))
        file.close()
        
    def get_byte(self, address):
        return self.data[address]
        
    def set_byte(self, address, value):
        self.data[address] = value

    def get_bytes(self, address, size):
        return self.data[address:address + size]
        
    def set_bytes(self, address, data):
        self.data[address:address + len(data)] = data

    def commit(self, filename = None):
        if not filename:
            filename = self.filename

        with open(filename, "wb") as file:
            file.write(self.data)

    def find_value(self, value, start_address, end_address):
        b1 = value & 0xFF
        b2 = (value >> 8) & 0xFF
        for address in range(start_address, end_address):
            if self.data[address] == b1 and self.data[address+1] == b2:
                return address

        return 0

    def get_pointers(self, address, count):
        pointers = {}
        while (count > 0):
            ptr = self.get_byte(address + 1) << 8 | self.get_byte(address)
            if ptr not in pointers:
                pointers[ptr] = [address]
            else:
                pointers[ptr].append(address)

            address += 2
            count -= 1

        return pointers
