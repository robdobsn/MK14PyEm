

import ins8060cpu

mem = [0xc4, 0x12, 0x00]
myCPU = ins8060cpu.CPU_INS8060(mem)
myCPU.run()
mem = [0xc0, 0xff, 0x00]
myCPU.reset(mem)
myCPU.run()
