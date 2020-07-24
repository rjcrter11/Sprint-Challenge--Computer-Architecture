"""CPU functionality."""

import sys
from datetime import datetime, timedelta
import time

# ops
HLT = 0b00000001
LDI = 0b10000010
PRN = 0b01000111
LD = 0b10000011
ST = 0b10000100
PUSH = 0b01000101
POP = 0b01000110
PRA = 0b01001000

# ALU ops
ADD = 0b10100000
SUB = 0b10100001
MUL = 0b10100010
DIV = 0b10100011
MOD = 0b10100100
INC = 0b01100101
DEC = 0b01100110
CMP = 0b10100111
AND = 0b10101000
NOT = 0b01101001
OR = 0b10101010
XOR = 0b10101011
SHL = 0b10101100
SHR = 0b10101101

# PC mutators
CALL = 0b01010000
RET = 0b00010001
INT = 0b01010010
IRET = 0b00010011
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110

# Stack pointer
SP = 7
# Interrupt status
IS = 6
# Interrupt mask
IM = 5


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0
        self.fl = 0
        self.running = True
        self.reg[SP] = 0xf4
        self.ie = True

        self.dispatchtable = {
            HLT: self.handle_HLT,
            LDI: self.handle_LDI,
            PRN: self.handle_PRN,
            PUSH: self.handle_PUSH,
            POP: self.handle_POP,
            CALL: self.handle_CALL,
            RET: self.handle_RET,
            LD: self.handle_LD,
            JMP: self.handle_JMP,
            PRA: self.handle_PRA,
            ST: self.handle_ST,
            IRET: self.handle_IRET,
            JEQ: self.handle_JEQ,
            JNE: self.handle_JNE,
        }

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    def handle_HLT(self):
        self.running = False

    def handle_LDI(self, a, b):
        self.reg[a] = b

    def handle_PRN(self, a):
        print(self.reg[a])

    def handle_PUSH(self, a):
        self.reg[SP] -= 1
        self.ram_write(self.reg[SP], self.reg[a])

    def handle_POP(self, a):
        self.reg[a] = self.ram_read(self.reg[SP])
        self.reg[SP] += 1

    def handle_CALL(self, a):
        self.reg[SP] -= 1
        self.ram_write(self.reg[SP], self.pc + 2)
        self.pc = self.reg[a]

    def handle_RET(self):
        self.pc = self.ram_read(self.reg[SP])
        self.reg[SP] += 1

    def handle_LD(self, a, b):
        self.reg[a] = self.ram_read(self.reg[b])

    def check_interrupts(self):
        masked_interrupts = self.reg[IM] & self.reg[IS]

        for i in range(8):
            interrupt_happened = ((masked_interrupts >> i) & 1) == 1

            if interrupt_happened:
                self.ie = False   # disable interrupts
                self.reg[IS] = 0  # clear IS
                self.reg[SP] -= 1  # push pc onto stack
                self.ram_write(self.reg[SP], self.pc)
                self.reg[SP] -= 1  # push flag onto stack
                self.ram_write(self.reg[SP], self.fl)
                for i in range(0, 7):  # push R0 - R6
                    self.reg[SP] -= 1
                    self.ram_write(self.reg[SP], self.reg[i])

                self.pc = self.ram[0xf8]

    def handle_JMP(self, a):
        self.pc = self.reg[a]

    def handle_JEQ(self, a):
        if self.fl & 0b1:
            self.pc = self.reg[a]
        else:
            self.pc += 2

    def handle_JNE(self, a):
        if not self.fl & 0b1:
            self.pc = self.reg[a]
        else:
            self.pc += 2

    def handle_PRA(self, a):
        print(chr(self.reg[a]), end='', flush=True)

    def handle_ST(self, a, b):
        self.ram_write(self.reg[a], self.reg[b])

    def handle_IRET(self):

        for i in range(6, -1, -1):  # Pop R6-R0
            self.reg[i] = self.ram_read(self.reg[SP])
            self.reg[SP] += 1
        self.fl = self.ram_read(self.reg[SP])  # pop flag
        self.reg[SP] += 1
        self.pc = self.ram_read(self.reg[SP])  # pop return address as pc
        self.reg[SP] += 1
        self.ie = True  # re-enable interrupt

    def load(self):
        """Load a program into memory."""
        file_name = f'examples/{sys.argv[1]}.ls8'
        try:
            address = 0
            with open(file_name) as f:
                for line in f:

                    command = line.split('#')[0].strip()

                    if command == '':
                        continue

                    instruction = int(command, 2)
                    self.ram_write(address, instruction)
                    address += 1

        except FileNotFoundError:
            print(f'{sys.argv[0]} : {sys.argv[1]} file was not found')
            sys.exit()

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        # flags: 00000LGE
        if op == ADD:
            self.reg[reg_a] += self.reg[reg_b]
        elif op == SUB:
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == MUL:
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == AND:
            result = self.reg[reg_a] & self.reg[reg_b]
            self.reg[reg_a] = result
        elif op == CMP:
            if self.reg[reg_a] == self.reg[reg_b]:
                self.fl = 0b1
            elif self.reg[reg_a] < self.reg[reg_b]:
                self.fl = 0b100
            else:
                self.fl = 0b010
        elif op == DIV:
            result = self.reg[reg_a] / self.reg[reg_b]
            if self.reg[reg_b] == 0:
                self.handle_HLT()
                raise Exception("Error. Second register is zero")
            else:
                self.reg[reg_a] = result
        elif op == INC:
            reg_b is None
            self.reg[reg_a] += 1
        elif op == DEC:
            reg_b is None
            self.reg[reg_a] -= 1

        elif op == MOD:
            result = self.reg[reg_a] % self.reg[reg_b]
            if self.reg[reg_b] == 0:
                self.handle_HLT()
                raise Exception("Error. Second register is zero")
            else:
                self.reg[reg_a] = result
        elif op == NOT:
            self.reg[reg_a] = ~ self.reg[reg_a]

        elif op == OR:
            result = self.reg[reg_a] | self.reg[reg_b]
            self.reg[reg_a] = result
        elif op == SHL:
            self.reg[reg_a] << self.reg[reg_b]
        elif op == SHR:
            self.reg[reg_a] >> self.reg[reg_b]
        elif op == SUB:
            result = self.reg[reg_a] - self.reg[reg_b]
            self.reg[reg_a] = result
        elif op == XOR:
            result = self.reg[reg_a] ^ self.reg[reg_b]
            self.reg[reg_a] = result

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X %02X %02X |" % (
            self.pc,
            self.fl,
            self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""

        start_time = time.time()
        while self.running:

            if self.ie:
                self.check_interrupts()

            check_time = time.time()
            if check_time - start_time > 1:
                self.reg[IS] = 0b00000001
                start_time = time.time()

            IR = self.ram_read(self.pc)
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            instructions = (IR >> 6) + 1
            direct_set_instructions = ((IR >> 4) & 0b1) == 1
            alu_op = ((IR >> 5) & 0b1) == 1

            if not direct_set_instructions:
                self.pc += instructions

            if alu_op:
                self.alu(IR, operand_a, operand_b)

            elif IR in self.dispatchtable:
                if instructions == 1:
                    self.dispatchtable[IR]()
                elif instructions == 2:
                    self.dispatchtable[IR](operand_a)
                else:
                    self.dispatchtable[IR](operand_a, operand_b)

            else:
                print(f'Invalid instruction {bin(IR)} at {hex(self.pc)}')
