

class MK14_MEMMAP:

    def __init__(self):
        self.stdRam = [0] * 256
        self.display = [0] * 8

    def getDisplayBits(self, n):
        return self.display[n]
    
    def read(self, addr):
        if addr & 0xf00 == 0xf00:
            return self.stdRam[addr - 0xf00]
        else:
            print("Read address unknown", format(addr, "04x"))
        return 0

    def write(self, addr, val):
        if addr & 0xf00 == 0xf00:
            self.stdRam[addr - 0xf00] = val & 0xff
        elif (addr & 0xf00) == 0x900 or (addr & 0xf00) == 0xd00:
            self.display[addr & 0x07] = val
#            print("Disp: ", end="")
#            for i in range(8):
#                print(format(self.display[7-i],"02x"),"",end="")
#            print()
        else:
            print("Write address unknown", format(addr, "04x"))

    def init(self, initialList):
        for memBlock in initialList:
            blkAddr = memBlock[0]
            blkData = memBlock[1]
            for i in range(len(blkData)):
                self.write(blkAddr+i, blkData[i])


