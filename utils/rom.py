from pathlib import Path

class ROM:
    def __init__(self, filename):
        self.filename = filename       

        self.size = Path(filename).stat().st_size
               
        file = open(filename, "rb")
        self.data = file.read(self.size)
        file.close()
        
    def get_byte(self, address):
        return self.data[address]
        
    def set_byte(self, address, value):
        self.data[address] = value

    def get_bytes(self, address, size):
        return self.data[address:address + size]
        
    def commit(self, filename = None):
        if not filename:
            filename = self.filename
            
        file = open(filename, "wb")
        file.write(self.data, self.size)
        file.close()
