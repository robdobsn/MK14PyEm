



class CPU:

    STOP = 0
    
    def __init__(self, memory):
        self.reset()
        self.memory = memory

    def reset(self):
        self.acc = 0
        self.ext = 0
        self.stat = 0
        self.cycles = 0
        self.ptrs = [0,0,0,0]

    def execAndCheckForExit(self):
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
            if opcode == self.STOP:
                print("Stopping at STOP")
                break

            self.showReg("before", opcode)
            self.processOpcode(opcode)
            self.showReg("after", opcode)

    def indexed(self, ptr):
        offset = self.fetchIP()
        if offset == 0x80:
            offset = self.ext
        elif offset & 0x80 != 0:
            offset = offset - 256
        idx = ((ptr + offset) & 0xfff) | (ptr & 0xf000)
        print("Idx", format(idx, '04x'))
        return idx

    def inRange(self, val, start, leng):
        return val >= start and val < start+leng

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
                self.memory[self.indexed(self.ptrs[ptrIdx])] = self.acc
            else:
                print("ST AUT")
                self.memory[self.autoIndexed(self.ptrs[ptrIdx])] = self.acc            
            return
        # Other ops require a "memory" value
        if idxType <= 3:
            mem = self.memory[self.indexed(self.ptrs[ptrIdx])]
            self.cycles += 18
            print("IDX", mem)
        elif idxType == 4:
            mem = self.fetchIP()
            self.cycles += 10
            print("IMM", mem)
        elif idxType <= 7:
            mem = self.memory[self.autoIndexed(self.ptrs[ptrIdx])]
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
        
        # ALU operations 0xc0 .. 0xff
        if self.inRange(opcode, 0xc0, 0x40):
            idxType = opcode & 0x07
            opType = opcode & 0x38
            self.doALU(opType, idxType, self.acc, opcode&0x03)
        elif self.inRange(opcode & 0x78, 0x40, 0x40) and opcode & 0x87 == 0:
            idxType = opcode & 8
            opType = opcode & 0x38
            self.doALU(opType, idxType, self.acc, opcode&0x03)
            
mem = [0xc4, 0x12, CPU.STOP]
myCPU = CPU(mem)
myCPU.execAndCheckForExit()
