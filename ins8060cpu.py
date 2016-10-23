

class CPU_INS8060:

    def __init__(self, memory):
        self.reset(memory)

    def reset(self, memory):
        self.acc = 0
        self.ext = 0
        self.stat = 0
        self.cycles = 0
        self.ptrs = [0,0,0,0]
        if memory != None:
            self.memory = memory

    def run(self):
        self.execSome(8192)
        # check for exit button and exit if so

    def fetchIP(self):
        op = self.memory[self.ptrs[0]]
        self.ptrs[0] += 1
        return op

    def showReg(self, debugStr, opcode):
        print(debugStr, format(self.acc, '02x'), format(self.ext, '02x'), format(self.stat, '02x'))
        print("   ", format(self.ptrs[0], '04x'), format(self.ptrs[1], '04x'), format(self.ptrs[2], '04x'), format(self.ptrs[3], '04x'))

    def execSome(self, numInstr):
        while (True):
            numInstr -= 1
            if numInstr <= 0:
                print("Done numInstrs")
                break

            opcode = self.fetchIP()
            
            self.showReg("before", opcode)
            bHalt = self.processOpcode(opcode)
            self.showReg("after", opcode)

            if bHalt:
                print("Stopping at HALT")
                break

    def indexed(self, ptrIdx):
        offset = self.fetchIP()
        if offset == 0x80:
            offset = self.ext
        elif offset & 0x80 != 0:
            offset = offset - 256
        ptr = self.ptrs[ptrIdx]
        addr = ((ptr + offset) & 0xfff) | (ptr & 0xf000)
        print("Addr", format(addr, '04x'))
        return addr

    def autoIndexed(self, ptrIdx):
        offset = self.fetchIP()
        if offset == 0x80:
            offset = self.ext
        elif offset & 0x80 != 0:
            offset = offset - 256
        if offset < 0:
            self.ptr[ptrIdx] = self.add12Bit(self.ptr[ptrIdx], offset)
        addr = self.ptrs[ptrIdx]
        if offset > 0:
            self.ptr[ptrIdx] = self.add12Bit(self.ptr[ptrIdx], offset)
        print("Addr", format(addr, '04x'))
        return addr

    def inRange(self, val, start, leng):
        return val >= start and val < start+leng

    def sign(self, n):
        return n & 0x80
    
    def decimalAdd(self, in1, in2):
        dOnes = in1 & 0x0f + in2 & 0x0f
        dTens = in1 * 0xf0 + in2 & 0xf0
        dOnes += 1 if (self.stat & 0x80 != 0) else 0
        self.stat &= 0x7f
        if dOnes > 9:
            dOnes = dOnes - 10
            dTens += 0x10
        if dTens > 0x90:
            dTens -= 0xa0
            self.stat |= 0x80
        outVal = dTens + dOnes
        return outVal & 0xff

    def binaryAdd(self, in1, in2):
        outVal = in1 + in2 + 1 if (self.stat & 0x80 != 0) else 0
        self.stat = self.stat & 0x3f # clear CYL and OV
        if outVal > 0xff:
            self.stat |= 0x80
        if self.sign(in1) == self.sign(in2) and self.sign(in1) != self.sign(outVal):
            self.stat |= 0x40
        return outVal & 0xff

    def complimentaryAdd(self, in1, in2):
        return binaryAdd(in1 ^ 0xff, in2)

    def doALU(self, opType, idxType, sourceVal, ptrIdx):
        print(opType)
        # Handle store
        if opType == 0x08: # opcodes are 0xc8..0xcf
            self.cycles += 18
            if idxType <= 3:
                print("ST IDX")
                self.memory[self.indexed(ptrIdx)] = self.acc
            else:
                print("ST AUT")
                self.memory[self.autoIndexed(ptrIdx)] = self.acc            
            return
        # Other ops require a "memory" value
        if idxType <= 3:
            mem = self.memory[self.indexed(ptrIdx)]
            self.cycles += 18
            print("IDX", mem)
        elif idxType == 4:
            mem = self.fetchIP()
            self.cycles += 10
            print("IMM", mem)
        elif idxType <= 7:
            mem = self.memory[self.autoIndexed(ptrIdx)]
            self.cycles += 18
            print("AUT", mem)
        else:
            mem = self.ext
            self.cycles += 6
            print("EXT", mem)
        # Perform the operation
        if opType == 0x00: # opcodes are 0xc0..0xc7
            self.acc = mem
            print("LD", self.acc)
        elif opType == 0x10:
            self.acc = mem & self.acc
            print("AND", self.acc)
        elif opType == 0x18:
            self.acc = mem | self.acc
            print("OR", self.acc)
        elif opType == 0x20:
            self.acc = mem ^ self.acc
            print("XOR", self.acc)
        elif opType == 0x28:
            self.acc = self.decimalAdd(mem, self.acc)
            self.cycles += 5
            print("DAD", self.acc)
        elif opType == 0x30:
            self.acc = self.binaryAdd(mem, self.acc)
            self.cycles += 1
            print("ADD", self.acc)
        elif opType == 0x38:
            self.acc = self.complimentaryAdd(mem, self.acc)        
            self.cycles += 2
            print("CAD", self.acc)
        
    def processOpcode(self, opcode):

        bHalt = False        
        # ALU operations 0xc0 .. 0xff
        if self.inRange(opcode, 0xc0, 0x40):
            idxType = opcode & 0x07
            opType = opcode & 0x38
            self.doALU(opType, idxType, self.acc, opcode&0x03)
        # ALU operations 0x40, 0x48, 0x50, .. 0x78
        elif self.inRange(opcode & 0x78, 0x40, 0x40) and opcode & 0x87 == 0:
            idxType = opcode & 8
            opType = opcode & 0x38
            self.doALU(opType, idxType, self.acc, opcode&0x03)
        # XPAL and XPAH
        elif self.inRange(opcode, 0x30, 8):
            ptr = self.ptrs[opcode&0x03]
            ptr &= 0xff00 if opcode < 0x34 else 0xff
            ptr |= self.acc if opcode < 0x34 else (self.acc << 8)
            self.ptrs[opcode&0x03] = ptr
            self.acc = ptr & 0xff
            self.cycles += 8
        # XPPC
        elif self.inRange(opcode, 0x3c, 4):
            ptr = self.ptrs[opcode&0x03]
            self.ptrs[opcode&0x03] = self.ptrs[0]
            self.ptrs[0] = ptr
            self.cycles += 7
        # Jumps
        elif self.inRange(opcode, 0x90, 16):
            jump = False
            if opcode < 0x94:
                jump = True
            elif opcode < 0x98:
                if self.acc & 0x80 == 0:
                    jump = True
            elif opcode < 0x9c:
                if self.acc == 0:
                    jump = True
            else:
                if self.acc != 0:
                    jump = True
            if jump:
                self.ptrs[0] = self.indexed(opcode&0x03)
            self.cycles += 11
        # ILD and DLD
        elif self.inRange(opcode, 0xa8, 8):
            ptr = self.indexed(opcode&0x03)
            self.acc = self.memory[ptr + (1 if opcode < 0xac else -1)]
            self.memory[ptr] = self.acc
            self.cycles += 22
        # DLY
        elif opcode == 0x8f:
            n = self.fetchIP()
            leng = n & 0xff
            leng = 13 + 2 * self.acc + 2 * n + 512 * n
            self.acc = 0xff
            self.cycles += leng
        # XAE
        elif opcode == 0x01:
            n = self.acc
            self.acc = self.ext
            self.ext = n
            self.cycles += 1
        # SIO
        elif opcode == 0x19:
            self.ext = (self.ext >> 1) & 0x7f
            self.cycles += 5
        # SR
        elif opcode == 0x1c:
            self.acc = (self.acc >> 1) & 0x7f
            self.cycles += 5
        # SRL
        elif opcode == 0x1d:
            self.acc = ((self.acc >> 1) & 0x7f) | (self.stat & 0x80)
            self.cycles += 5
        # RR
        elif opcode == 0x1e:
            self.acc = ((self.acc >> 1) & 0x7f) | (0x80 if (self.acc & 0x01 == 1) else 0)
            self.cycles += 5
        # RRL
        elif opcode == 0x1f:
            n = self.acc
            self.acc = ((self.acc >> 1) & 0x7f) | (0x80 if (self.stat & 0x80 != 0) else 0)
            self.stat = (self.stat & 0x7f) | (0x80 if (n & 0x01 == 1) else 0)
            self.cycles += 5
        # HALT
        elif opcode == 0x00:
            bHalt = True
            self.cycles += 8
        # CCL
        elif opcode == 0x02:
            self.stat &= 0x7f
            self.cycles += 5
        # SCL
        elif opcode == 0x03:
            self.stat |= 0x80
            self.cycles += 5
        # DINT
        elif opcode == 0x03:
            self.stat &= 0xf7
            self.cycles += 6
        # IEN
        elif opcode == 0x03:
            self.stat |= 0x08
            self.cycles += 6
        # CSA
        elif opcode == 0x06:
            self.acc = self.stat
            self.cycles += 5
        # CAS
        elif opcode == 0x07:
            self.stat = self.acc & 0xcf
            self.cycles += 5
        # NOP
        elif opcode == 0x08:
            self.cycles += 1

        return bHalt

            



