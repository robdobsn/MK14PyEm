

class MK14_MEMMAP:

    def __init__(self, getCyclesFn):
        self.getCyclesFn = getCyclesFn
        self.stdRam = [0] * 256
        self.display = [0] * 8
        self.dispSetCycTime = [0] * 8
        self.btnMap = [0xff] * 8
        self.rom = [0] * 512

    def getDisplaySegments(self, n):
        return (self.display[n], self.dispSetCycTime[n])

    def doButtonMap(self, addr, bit, isPressed):
        if isPressed:
            mask = (1 << bit) ^ 0xff
            self.btnMap[addr] &= mask
        else:
            mask = 1 << bit
            self.btnMap[addr] |= mask
#        print("ButtonAddr", addr, self.btnMap[addr], isPressed)

    def setButton(self, buttonStr, isPressed):
        if buttonStr == "ABT":
            self.doButtonMap(4, 5, isPressed)
        elif buttonStr == "TRM":
            self.doButtonMap(7, 5, isPressed)
        elif buttonStr == "MEM":
            self.doButtonMap(3, 5, isPressed)
        elif buttonStr == "GO":
            self.doButtonMap(2, 5, isPressed)
        else:
            buttonCode = int(buttonStr, 16)
            if buttonCode < 8:
                self.doButtonMap(buttonCode, 7, isPressed)
            elif buttonCode < 10:
                self.doButtonMap(buttonCode-8, 6, isPressed)
            elif buttonCode < 0x0e:
                self.doButtonMap(buttonCode - 10, 4, isPressed)
            else:
                self.doButtonMap(buttonCode - 10 + 2, 4, isPressed)

    def read(self, addr):
        page = addr & 0xf00
        if page == 0xf00:
            return self.stdRam[addr - 0xf00]
        elif page == 0x900 or page == 0xd00:
            if addr & 0x0f <= 0x07:
#                print("Read keyboard", addr, "rslt", self.btnMap[addr & 0x07])
                return self.btnMap[addr & 0x07]
            else:
                return 0xff
        elif page < 0x900:
            return self.rom[addr & 0x01ff]
        else:
            print("Read address unknown", format(addr, "04x"))
        return 0

    def write(self, addr, val, overwriteROM = False):
        page = addr & 0xf00
        if page == 0xf00:
            self.stdRam[addr - 0xf00] = val & 0xff
        elif page == 0x900 or page == 0xd00:
            if addr & 0x0f <= 0x07:
                self.display[addr & 0x07] = val
                self.dispSetCycTime[addr & 0x07] = self.getCyclesFn()
    #            print("Disp: ", end="")
    #            for i in range(8):
    #                print(format(self.display[7-i],"02x"),"",end="")
    #            print()
        elif page < 0x900:
            self.rom[addr & 0x01ff] = val & 0xff
        else:
            print("Write address unknown", format(addr, "04x"))

    def init(self, initialList):
        for memBlock in initialList:
            blkAddr = memBlock[0]
            blkData = memBlock[1]
            for i in range(len(blkData)):
                self.write(blkAddr+i, blkData[i], True)

