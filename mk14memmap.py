

class MK14_MEMMAP:

    def __init__(self):
        self.stdRam = [0] * 256

    def read(self, addr):
        if addr & 0xf00 == 0xf00:
            return self.stdRam[addr - 0xf00]
        return 0

    def write(self, addr, val):
        if addr & 0xf00 == 0xf00:
            self.stdRam[addr - 0xf00] = val & 0xff

    def init(self, initialList):
        for memBlock in initialList:
            blkAddr = memBlock[0]
            blkData = memBlock[1]
            for i in range(len(blkData)):
                self.write(blkAddr+i, blkData[i])


