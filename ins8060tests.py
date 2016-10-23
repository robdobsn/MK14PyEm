

import ins8060cpu
import unittest

HALT = 0x00
LD0 = 0xc0
LD1 = 0xc1
LD2 = 0xc2
LD3 = 0xc3
LDI = 0xc4
LDAT1 = 0xc5
LDAT2 = 0xc6
LDAT3 = 0xc7
ST0 = 0xc8
ST1 = 0xc9
ST2 = 0xca
ST3 = 0xcb
CCL = 0x02
XPAL0 = 0x30
XPAL1 = 0x31
XPAL2 = 0x32
XPAL3 = 0x33
XPAH0 = 0x34
XPAH1 = 0x35
XPAH2 = 0x36
XPAH3 = 0x37
RR = 0x1e
RRL = 0x1f
ADD0 = 0xf0
ADD1 = 0xf1
ADD2 = 0xf2
ADD3 = 0xf3
XPPC3 = 0x3f
JP = 0x94
JNZ = 0x9c
JMP = 0x90
DLD2 = 0xba

def toBCD(v1):
    return ((v1 // 10) % 10) * 16 + (v1 % 10)

def bcdCarry(v1):
    return v1 >= 100

def showProg(mem):
    for m in mem:
        print(format(m, "02x"), end=" ")
    print()

def showMem(mem, addr, leng):
    for i in range(leng):
        if i % 16 == 0:
            print(format(addr+i, "04x"), "", end="")
        print(format(mem.read(addr+i), "02x"), "", end="")
        if i % 16 == 15:
            print()
    print()

def hexVal(inStr, pos, len):
    return int(inStr[pos:pos+len], 16)
    
def fromHexLines(hexLines):
    memOut = []
    for hexLine in hexLines:
        leng = hexVal(hexLine, 1, 2)
        if leng > 0:
            addr = hexVal(hexLine, 3, 4)
            memVals = []
            for i in range(leng):
                memVals.append(hexVal(hexLine, 9+i*2, 2))
            memOut.append([addr, memVals])
    return memOut
        
class Test8060(unittest.TestCase):

    def setUp(self):
        #print("--------------------------------")
        pass
        
    def test_LDI(self):
        v1 = 0x33
        mem = [(0xf00, [LDI, v1, HALT])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf00)
        self.assertEqual(self.cpu.acc, v1)

    def test_LDIX(self):
        v1 = 0x46
        v2 = 0x99
        mem = [(0xf00, [v2, LD0, 1, HALT, v1])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf01)
        self.assertEqual(self.cpu.acc, v1)
        v1 = 0xc2
        mem = [(0xf00, [v1, LD0, 0xfd, 0x00])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf01)
        self.assertEqual(self.cpu.acc, v1)

    def test_LDAT(self):
        p1 = 0x0f0a
        v1 = 0xb1
        o1 = 3
        mem = [(0xf00, [0x99, LDI, p1 & 0xff, XPAL1, LDI, p1 >> 8, XPAH1, LDAT1, o1, 0x00, v1])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf01)
        self.assertEqual(self.cpu.acc, v1)
        self.assertEqual(self.cpu.ptrs[1], p1 + o1)
        p1 = 0x0f0a
        v1 = 0xb1
        v2 = 0x99
        o1 = 0xf6
        mem = [(0xf00, [v2, LDI, p1 & 0xff, XPAL1, LDI, p1 >> 8, XPAH1, LDAT1, o1, 0x00, v1])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf01)
        self.assertEqual(self.cpu.acc, v2)
        self.assertEqual(self.cpu.ptrs[1], p1 - (256-o1))

    def test_DAD(self):
        v1 = 33
        v2 = 46
        mem = [(0xf00, [LDI, toBCD(v1), 0xec, toBCD(v2), 0x00])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf00)
        self.assertEqual(self.cpu.acc, toBCD(v1+v2))
        self.assertEqual((self.cpu.stat & 0x80) != 0, bcdCarry(v1+v2))
        v1 = 77
        mem = [(0xf00, [LDI, toBCD(v1), 0xec, toBCD(v2), 0x00])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf00)
        self.assertEqual(self.cpu.acc, toBCD(v1+v2))
        self.assertEqual((self.cpu.stat & 0x80) != 0, bcdCarry(v1+v2))
        v1 = 63
        mem = [(0xf00, [0x03, LDI, toBCD(v1), 0xec, toBCD(v2), 0x00])]
        self.cpu = ins8060cpu.CPU_INS8060(mem)
        self.cpu.run(0xf00)
        self.assertEqual(self.cpu.acc, toBCD(v1+v2+1))
        self.assertEqual((self.cpu.stat & 0x80) != 0, bcdCarry(v1+v2+1))

    def test_MULTIPLY16(self):
        v1 = 255
        v2 = 255
        memData = (0xf00, [0x00, v1, v2, 0, 0])
        memCode = (0xf4a, [LDI, 0x0f, XPAH2, LDI, 0x01, XPAL2, \
               LDI, 0x08, ST2, 0xff, LDI, 0, ST2, 2, ST2, 3, \
               LD2, 1, CCL, RR, ST2, 1, JP, 0x13, LD2, 2, ADD2, 00, RRL, ST2, 2, \
               LD2, 3, RRL, ST2, 3, DLD2, 0xff, JNZ, 0xe8, XPPC3, JMP, 0xdb, LD2, \
               2, JMP, 0xed, 0x00])
#        showProg(memCode[1])
        self.cpu = ins8060cpu.CPU_INS8060([memData, memCode], False, {"base":0xf00,"count":5})
        self.cpu.run(0xf4a)
        self.assertEqual(self.cpu.mem.read(0xf03), 0xfe)
        self.assertEqual(self.cpu.mem.read(0xf04), 0x01)

    def test_DIVIDE16(self):
        v1 = 12345
        v2 = 27
        memData = (0xf00, [0x00, v2, v1 >> 8, v1 & 0xff])
        memSetup = (0xf7a, [LDI, 0x0f, XPAH2, LDI, 0x01, XPAL2])
        hexLines = [":180F8000C20001C400CA00CAFFC2010378CA011D9404AA0090F3C20191",
                    ":180F980070CA01C2020378CA02C201FC00CA011D9404AAFF90EDC202D2",
                    ":0A0FB00070CA02C2FFCA013F90C6DA",
                    ":00000001FF"]
        memVals = fromHexLines(hexLines)
        memVals.append(memData)
        memVals.append(memSetup)
        #showProg(memCode[1])
        self.cpu = ins8060cpu.CPU_INS8060(memVals, False, {"base":0xf00,"count":5})
#        showMem(self.cpu.mem, 0xf00, 256)
        self.cpu.run(0xf7a)
#        showMem(self.cpu.mem, 0xf00, 5)
#        q = self.cpu.mem.read(0xf01) * 256 + self.cpu.mem.read(0xf02)
#        r = self.cpu.mem.read(0xf03)
#        print("q,r", q, r, end="")
        self.assertEqual(self.cpu.mem.read(0xf01) * 256 + self.cpu.mem.read(0xf02), v1 // v2)
        self.assertEqual(self.cpu.mem.read(0xf03), v1 % v2)
                
        
        
#    def test_split(self):
#        s = 'hello world'
#        self.assertEqual(s.split(), ['hello', 'world'])
#        # check that s.split fails when the separator is not a string
#        with self.assertRaises(TypeError):
#            s.split(2)

if __name__ == '__main__':
    unittest.main()
