
import mk14memmap

class CPU_INS8060:

    def __init__(self, initRAMList, initIP = 0, debugOn = False, debugRam = None):
        self.debugRam = debugRam
        self.debugOn = debugOn
        self.reset(initRAMList, initIP)

    def reset(self, initRAMList, initIP):
        if self.debugOn:
            print("")
            print("Reset")
        self.halted = False
        self.acc = 0
        self.ext = 0
        self.stat = 0
        self.cycles = 0
        self.ptrs = [initIP,0,0,0]
        self.mem = mk14memmap.MK14_MEMMAP(self.getCycles)
        if self.debugOn:
            print(initRAMList)
        self.mem.init(initRAMList)
        self.showReg("")

    def getCycles(self):
        return self.cycles

    def run(self, start = None):
        if start != None:
            self.ptrs[0] = start
        self.execSome(8192)
        # check for exit button and exit if so

    def service(self):
        self.execSome(10)

    def getMemMap(self):
        return self.mem
    
    def fetchIP(self):
        op = self.mem.read(self.ptrs[0])
        self.ptrs[0] += 1
        return op

    def showReg(self, debugStr):
        if self.debugOn:
            print(debugStr, format(self.acc, '02x'), \
                  format(self.ext, '02x'), format(self.stat, '02x'),\
                  end = "")
            print("", format(self.ptrs[0], '04x'), format(self.ptrs[1], '04x'),\
                  format(self.ptrs[2], '04x'), format(self.ptrs[3], '04x'),\
                  end = "")
            if self.debugRam != None:
                print(" @" + format(self.debugRam["base"], "04x") + " ", end="")
                for i in range(self.debugRam["count"]):
                    print(format(self.mem.read(self.debugRam["base"]+i), "02x"), "", end="")
            print()

    def execSome(self, numInstr):
        # Check that CPU has not halted
        if self.halted:
            return

        # Run in a loop until yield or halt
        while (True):
            debugIpAddr = self.ptrs[0]
            opcode = self.fetchIP()

            if self.debugOn:
                print("IP", format(debugIpAddr, "04x"), "OP", format(opcode, "02x"), end="")
            bHalt, debugStr = self.processOpcode(opcode)
            if self.debugOn:
                print("", '{:<14}'.format(debugStr), end="")
            self.showReg("")

            if bHalt:
                self.halted = True
                if self.debugOn:
                    print("Stopping at HALT")
                break

            numInstr -= 1
            if numInstr <= 0:
#                if self.debugOn:
#                    print("Yielding ... Done numInstrs")
                break

    def addr12bit(self, ptr, ofs):
        return ((ptr+ofs) & 0xFFF) | (ptr & 0xF000)
        
    def indexed(self, ptrIdx):
        offset = self.fetchIP()
#        print("IDX", format(offset, "02x"), "ptrIdx", ptrIdx, "ptr", format(self.ptrs[ptrIdx], "04x"))
        if offset == 0x80:
            offset = self.ext
        elif offset & 0x80 != 0:
            offset = offset - 256
        ptr = self.ptrs[ptrIdx]
        if ptrIdx == 0:  # IP has already incremented so fix this
            ptr -= 1
        addr = self.addr12bit(ptr, offset)
        return addr

    def autoIndexed(self, ptrIdx):
        oOffset = self.fetchIP()
        offset = oOffset
        if offset == 0x80:
            offset = self.ext
        elif offset & 0x80 != 0:
            offset = offset - 256
        if offset < 0:
            self.ptrs[ptrIdx] = self.addr12bit(self.ptrs[ptrIdx], offset)
        addr = self.ptrs[ptrIdx]
        if offset > 0:
            self.ptrs[ptrIdx] = self.addr12bit(self.ptrs[ptrIdx], offset)
#        print("@IX", format(oOffset, "02x"), format(offset, "02x"), "ptrIdx", ptrIdx, "ptr", format(self.ptrs[ptrIdx], "04x"))
        return addr

    def inRange(self, val, start, leng):
        return val >= start and val < start+leng

    def sign(self, n):
        return n & 0x80
    
    def decimalAdd(self, in1, in2):
        dOnes = (in1 & 0x0f) + (in2 & 0x0f)
        dTens = (in1 & 0xf0) + (in2 & 0xf0)
        dOnes += 1 if (self.stat & 0x80 != 0) else 0
        self.stat &= 0x7f
        if dOnes > 9:
            dOnes = dOnes - 10
            dTens += 0x10
        if dTens > 0x90:
            dTens -= 0xa0
            self.stat |= 0x80
        outVal = dTens + dOnes
        if self.debugOn:
            print("DecAdd", format(in1,"02x"), format(in2,"02x"), dOnes, dTens, outVal & 0xff)
        return outVal & 0xff

    def binaryAdd(self, in1, in2):
        outVal = in1 + in2 + (1 if (self.stat & 0x80 != 0) else 0)
        self.stat = self.stat & 0x3f # clear CYL and OV
        if outVal > 0xff:
            self.stat |= 0x80
        if self.sign(in1) == self.sign(in2) and self.sign(in1) != self.sign(outVal):
            self.stat |= 0x40
        return outVal & 0xff

    def complimentaryAdd(self, in1, in2):
        return self.binaryAdd(in1 ^ 0xff, in2)

    def doALU(self, opType, idxType, sourceVal, ptrIdx):
        debugStr = ""
        # Handle store
        if opType == 0x08: # opcodes are 0xc8..0xcf
            self.cycles += 18
            if idxType <= 3:
                addr = self.indexed(ptrIdx)
                debugStr += "ST " + format(addr, "04x") + ", " + format(self.acc, "02x")
                self.mem.write(addr, self.acc)
            else:
                addr = self.autoIndexed(ptrIdx)
                debugStr += "ST@ " + format(addr, "04x") + ", " + format(self.acc, "02x")
                self.mem.write(addr, self.acc)
            return debugStr
        # Other ops require a "memory" value
        if idxType <= 3:
            addr = self.indexed(ptrIdx)
            mem = self.mem.read(addr)
            self.cycles += 18
            debugStr += " " + format(addr, "04x") + " => " + format(mem, "02x")
        elif idxType == 4:
            mem = self.fetchIP()
            self.cycles += 10
            debugStr += "I " + format(mem, "02x")
        elif idxType <= 7:
            addr = self.autoIndexed(ptrIdx)
            mem = self.mem.read(addr)
            self.cycles += 18
            debugStr += "@ " + format(addr, "04x") + " => " + format(mem, "02x")
        else:
            mem = self.ext
            self.cycles += 6
            debugStr += "E " + format(mem, "02x")
        # Perform the operation
        if opType == 0x00: # opcodes are 0xc0..0xc7
            self.acc = mem
            debugStr = "LD" + debugStr
        elif opType == 0x10:
            self.acc = mem & self.acc
            debugStr = "AND" + debugStr
        elif opType == 0x18:
            self.acc = mem | self.acc
            debugStr = "OR" + debugStr
        elif opType == 0x20:
            self.acc = mem ^ self.acc
            debugStr = "XOR" + debugStr
        elif opType == 0x28:
            self.acc = self.decimalAdd(mem, self.acc)
            self.cycles += 5
            debugStr = "DAD" + debugStr
        elif opType == 0x30:
            self.acc = self.binaryAdd(mem, self.acc)
            self.cycles += 1
            debugStr = "ADD" + debugStr
        elif opType == 0x38:
            self.acc = self.complimentaryAdd(mem, self.acc)        
            self.cycles += 2
            debugStr = "CAD" + debugStr
        return debugStr
        
    def processOpcode(self, opcode):
        bHalt = False
        debugStr = ""
        # ALU operations 0xc0 .. 0xff
        if self.inRange(opcode, 0xc0, 0x40):
            idxType = opcode & 0x07
            opType = opcode & 0x38
            debugStr = self.doALU(opType, idxType, self.acc, opcode&0x03)
        # ALU operations 0x40, 0x48, 0x50, .. 0x78
        elif self.inRange(opcode & 0x78, 0x40, 0x40) and opcode & 0x87 == 0:
            idxType = 8
            opType = opcode & 0x38
            debugStr = self.doALU(opType, idxType, self.acc, opcode&0x03)
        # XPAL and XPAH
        elif self.inRange(opcode, 0x30, 8):
            ptr = self.ptrs[opcode&0x03]
            ptr &= 0xff00 if opcode < 0x34 else 0xff
            ptr |= self.acc if opcode < 0x34 else (self.acc << 8)
            self.ptrs[opcode&0x03] = ptr
            self.acc = ptr & 0xff
            self.cycles += 8
            debugStr = "XPAL" if opcode < 0x34 else "XPAH"
            debugStr += str(opcode&0x03)
        # XPPC
        elif self.inRange(opcode, 0x3c, 4):
            ptr = self.ptrs[opcode&0x03]
            self.ptrs[opcode&0x03] = self.ptrs[0]
            self.ptrs[0] = ptr
            self.cycles += 7
            debugStr = "XPPC" + str(opcode&0x03)
        # Jumps
        elif self.inRange(opcode, 0x90, 16):
            jump = False
            if opcode < 0x94:
                jump = True
                debugStr = "JMP"
            elif opcode < 0x98:
                if self.acc & 0x80 == 0:
                    jump = True
                    debugStr = "JP True"
                else:
                    debugStr = "JP False"
            elif opcode < 0x9c:
                if self.acc == 0:
                    jump = True
                    debugStr = "JZ True"
                else:
                    debugStr = "JZ False"
            else:
                if self.acc != 0:
                    jump = True
                    debugStr = "JNZ True"
                else:
                    debugStr = "JNZ False"
            if jump:
                self.ptrs[0] = self.indexed(opcode&0x03) + 1
            else:
                self.ptrs[0] += 1
            self.cycles += 11
        # ILD
        elif self.inRange(opcode, 0xa8, 4):
            ptr = self.indexed(opcode&0x03)
            self.acc = (self.mem.read(ptr) + 1) & 0xff
            self.mem.write(ptr, self.acc)
            self.cycles += 22
            debugStr = "ILD"
            debugStr += str(opcode&0x03)
        # DLD
        elif self.inRange(opcode, 0xb8, 4):
            ptr = self.indexed(opcode&0x03)
            self.acc = (self.mem.read(ptr) - 1) & 0xff
            self.mem.write(ptr, self.acc)
            self.cycles += 22
            debugStr = "DLD"
            debugStr += str(opcode&0x03)
        # DLY
        elif opcode == 0x8f:
            n = self.fetchIP()
            leng = n & 0xff
            leng = 13 + 2 * self.acc + 2 * n + 512 * n
            self.acc = 0xff
            self.cycles += leng
            debugStr = "DLY"
        # XAE
        elif opcode == 0x01:
            n = self.acc
            self.acc = self.ext
            self.ext = n
            self.cycles += 1
            debugStr = "XAE"
        # SIO
        elif opcode == 0x19:
            self.ext = (self.ext >> 1) & 0x7f
            self.cycles += 5
            debugStr = "SIO"
        # SR
        elif opcode == 0x1c:
            self.acc = (self.acc >> 1) & 0x7f
            self.cycles += 5
            debugStr = "SR"
        # SRL
        elif opcode == 0x1d:
            self.acc = ((self.acc >> 1) & 0x7f) | (self.stat & 0x80)
            self.cycles += 5
            debugStr = "SRL"
        # RR
        elif opcode == 0x1e:
            self.acc = ((self.acc >> 1) & 0x7f) | (0x80 if (self.acc & 0x01 == 1) else 0)
            self.cycles += 5
            debugStr = "RR"
        # RRL
        elif opcode == 0x1f:
            n = self.acc
            self.acc = ((self.acc >> 1) & 0x7f) | (0x80 if (self.stat & 0x80 != 0) else 0)
            self.stat = (self.stat & 0x7f) | (0x80 if (n & 0x01 == 1) else 0)
            self.cycles += 5
            debugStr = "RRL"
        # HALT
        elif opcode == 0x00:
            bHalt = True
            self.cycles += 8
        # CCL
        elif opcode == 0x02:
            self.stat &= 0x7f
            self.cycles += 5
            debugStr = "CCL"
        # SCL
        elif opcode == 0x03:
            self.stat |= 0x80
            self.cycles += 5
            debugStr = "SCL"
        # DINT
        elif opcode == 0x03:
            self.stat &= 0xf7
            self.cycles += 6
            debugStr = "DINT"
        # IEN
        elif opcode == 0x03:
            self.stat |= 0x08
            self.cycles += 6
            debugStr = "IEN"
        # CSA
        elif opcode == 0x06:
            self.acc = self.stat
            self.cycles += 5
            debugStr = "CSA"
        # CAS
        elif opcode == 0x07:
            self.stat = self.acc & 0xcf
            self.cycles += 5
            debugStr = "CAS"
        # NOP
        elif opcode == 0x08:
            self.cycles += 1
            debugStr = "NOP"
        # Unknown
        else:
            debugStr = "UNKNOWN " + format(opcode, "02x")

        return (bHalt, debugStr)
