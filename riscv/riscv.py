#!/home/bensch98/.conda/envs/riscv/bin/python
import glob
import struct
from elftools.elf.elffile import ELFFile

regnames = \
    ['x0', 'ra', 'sp', 'gp', 'tp'] + [f't{i}' for i in range(0, 3)] + ['s0', 's1'] + \
    [f'a{i}' for i in range(0, 8)] + \
    [f's{i}' for i in range(2, 12)] + \
    [f't{i}' for i in range(3, 7)] + ['PC']

class Regfile:
    def __init__(self):
        self.regs = [0]*33
    def __getitem__(self, key):
        return self.regs[key]
    def __setitem__(self, key, value):
        if key == 0:
            return
        self.regs[key] = value & 0xffffffff

PC = 32

regfile = None
memory = None
def reset():
    global regfile, memory
    regfile = Regfile()
    # 1 byte times 65536 = 64k RAM at 0x80000000
    memory = bytes(b'\x00' * 0x10000)

from enum import Enum
# RC32I Base Instruction Set
class Ops(Enum):
    LUI    = 0b0110111 # LUI
    LOAD   = 0b0000011 # LB[U], LH[U], LW
    STORE  = 0b0100011 # SB, SH, SW

    AUIPC  = 0b0010111 # AUIPC
    BRANCH = 0b1100011 # BEQ, BNE, BLT, BLT[U], BGE[U] 
    JAL    = 0b1101111 # JAL
    JALR   = 0b1100111 # JALR

    IMM    = 0b0010011 # ADDI, SLTI, ANDI, ORI, XORI, SLLI, SRLI, SRAI
    OP     = 0b0110011 # ADD, SLT[U], AND, OR, XOR, SLL, SRL, SUB, SRA

    MISC   = 0b0001111 # FENCE
    SYSTEM = 0b1110011 # ECALL, EBREAK

class Funct3(Enum):
    ADD = SUB = ADDI = 0b000
    SLLI  = 0b001
    SLT = SLTI = 0b010
    SLTU = SLTIU = 0b011

    XOR = XORI = 0b100
    SRL = SRLI = SRA = SRAI = 0b101
    OR = ORI = 0b110
    AND = ANDI = 0b111

    BEQ = 0b000
    BNE = 0b001
    BLT = 0b100
    BGE = 0b101
    BLTU = 0b110
    BGEU = 0b111

    LB = SB = 0b000
    LH = SH = 0b001
    LW = SW = 0b010
    LBU = 0b100
    LHU = 0b101

    # stupid instructions below this line
    ECALL = 0b000
    CSRRW = 0b001
    CSRRS = 0b010
    CSRRC = 0b011
    CSRRWI = 0b101
    CSRRSI = 0b110
    CSRRCI = 0b111


def ws(addr, dat):
    global memory
    # print(hex(addr), len(dat))
    addr -= 0x80000000
    assert addr >= 0 and addr < len(memory)
    memory = memory[:addr] + dat + memory[addr+len(dat):]

def r32(addr):
    addr -= 0x80000000
    if addr < 0 or addr >= len(memory):
        raise Exception(f"Read out of bounds: 0x{addr}")
    return struct.unpack("<I", memory[addr:addr+4])[0]

def dump():
    pp = []
    for i in range(33):
        if i != 0 and i % 8 == 0:
            pp.append('\n')
        pp.append(f"{regnames[i]:>4}: {regfile[i]:08x}")
    print(''.join(pp), '\n')

def sign_extend(x, l):
    if x >> (l-1) == 1:
        return -((1 << l) - x)
    else:
        return x

def arith(funct3, x, y):
    if funct3 == Funct3.ADDI:
        return x + y
    elif funct3 == Funct3.SLLI:
        return x << (y & 0x1f)
    elif funct3 == Funct3.SRLI:
        return x >> (y & 0x1f)
    elif funct3 == Funct3.ORI:
        return x | y
    elif funct3 == Funct3.XORI:
        return x ^ y
    elif funct3 == Funct3.ANDI:
        return x & y
    elif funct3 == Funct3.SLT:
        return int(sign_extend(x, 32) < sign_extend(y, 32))
    elif funct3 == Funct3.SLTU:
        return int(x & 0xffffffff < y & 0xffffffff)
    else:
        dump()
        raise Exception(f"write arith funct3 {funct3}/{funct3.value:03b}")

def step():
    # Instruction Fetch
    ins = r32(regfile[PC])
    def gibi(s, e):
        return (ins >> e) & ((1 << (s - e + 1)) - 1)

    # Instruction Decode
    opcode = Ops(gibi(6, 0)) # 0b1111111
    #print(f"<PC: 0x{regfile[PC]:08x} | INS: 0x{ins:08x} | Ops.{opcode.name}: 0b{opcode.value:07b}>")
    if opcode == Ops.JAL:
        # J-type instruction
        rd = gibi(11, 7)
        offset = sign_extend(gibi(32, 31) << 20 | gibi(30, 21) << 1 | gibi(21, 20) << 11 | gibi(19, 12) << 12, 21)
        regfile[rd] = regfile[PC] + 4
        regfile[PC] += offset
        return True
    elif opcode == Ops.JALR:
        # I-type instruction
        rd = gibi(11, 7)
        rs1 = gibi(19, 15)
        imm = sign_extend(gibi(31, 20), 12)
        nv = regfile[PC] + 4
        regfile[PC] = regfile[rs1] + imm
        regfile[rd] = nv
        return True
    elif opcode == Ops.LUI:
        # U-type instruction
        rd = gibi(11, 7)
        imm = gibi(31, 12)
        regfile[rd] = imm << 12
    elif opcode == Ops.AUIPC:
        # U-type instruction
        rd = gibi(11, 7)
        imm = gibi(31, 12)
        regfile[rd] = regfile[PC] + sign_extend(imm << 12, 32)
    elif opcode == Ops.OP:
        # R-type instruction
        rd = gibi(11, 7)
        rs1 = gibi(19, 15)
        rs2 = gibi(24, 20)
        funct3 = Funct3(gibi(14, 12))
        funct7 = gibi(31, 25)
        if funct3 == Funct3.ADD and funct7 == 0b0100000:
            # this is sub
            regfile[rd] = regfile[rs1] - regfile[rs2]
        elif funct3 == Funct3.SRA and funct7 == 0b0100000:
            # this is sra
            shift = regfile[rs2] & 0x1f
            sb = regfile[rs1] >> 31
            out = regfile[rs1] >> shift
            out |= (0xffffffff * sb) << (32 - shift)
            regfile[rd] = out
        else:
            regfile[rd] = arith(funct3, regfile[rs1], regfile[rs2])
    elif opcode == Ops.IMM:
        # I-type instruction
        rd = gibi(11, 7)
        rs1 = gibi(19, 15)
        imm = sign_extend(gibi(31, 20), 12)
        funct3 = Funct3(gibi(14, 12))
        funct7 = gibi(31, 25)
        if funct3 == Funct3.SRAI and funct7 == 0b0100000:
            # this is srai
            sb = regfile[rs1] >> 31
            out = regfile[rs1] >> gibi(24, 20)
            out |= (0xffffffff * sb) << (32 - gibi(24, 20))
            regfile[rd] = out
        else:
            regfile[rd] = arith(funct3, regfile[rs1], imm)
    elif opcode == Ops.BRANCH:
        # B-type instruction
        rs1 = gibi(19, 15)
        rs2 = gibi(24, 20)
        funct3 = Funct3(gibi(14, 12))
        offset = sign_extend(gibi(32, 31) << 12 | gibi(30, 25) << 5 | gibi(11, 8) << 1 | gibi(8, 7) << 11, 13)
        cond = False
        if funct3 == Funct3.BEQ:
            cond = regfile[rs1] == regfile[rs2]
        elif funct3 == Funct3.BNE:
            cond = regfile[rs1] != regfile[rs2]
        elif funct3 == Funct3.BLT:
            cond = sign_extend(regfile[rs1], 32) < sign_extend(regfile[rs2], 32)
        elif funct3 == Funct3.BGE:
            cond = sign_extend(regfile[rs1], 32) >= sign_extend(regfile[rs2], 32)
        elif funct3 == Funct3.BLTU:
            cond = regfile[rs1] < regfile[rs2]
        elif funct3 == Funct3.BGEU:
            cond = regfile[rs1] >= regfile[rs2]
        else:
            dump()
            raise Exception(f"Write opcode/funct3: {opcode}/{opcode.value:07b}/{funct3.value:03b}")
        if cond:
            regfile[PC] += offset
            return True
    elif opcode == Ops.LOAD:
        # I-type instruction
        rd = gibi(11, 7)
        rs1 = gibi(19, 15)
        funct3 = Funct3(gibi(14, 12))
        imm = sign_extend(gibi(31, 20), 12)
        addr = regfile[rs1] + imm 
        if funct3 == Funct3.LB:
            regfile[rd] = sign_extend(r32(addr) & 0xff, 8)
        elif funct3 == Funct3.LH:
            regfile[rd] = sign_extend(r32(addr) & 0xffff, 16)
        elif funct3 == Funct3.LW:
            regfile[rd] = r32(addr)
        elif funct3 == Funct3.LBU:
            regfile[rd] = r32(addr) & 0xff
        elif funct3 == Funct3.LHU:
            regfile[rd] = r32(addr) & 0xffff
    elif opcode == Ops.STORE:
        # S-type instruction
        rs1 = gibi(19, 15)
        rs2 = gibi(24, 20)
        funct3 = Funct3(gibi(14, 12))
        offset = sign_extend(gibi(31, 25) << 5 | gibi(11, 7) << 0, 12)
        addr = regfile[rs1] + offset
        value = regfile[rs2]
        if funct3 == Funct3.SB:
            ws(addr, struct.pack("B", value & 0xff))
        elif funct3 == Funct3.SH:
            ws(addr, struct.pack("H", value & 0xffff))
        elif funct3 == Funct3.SW:
            ws(addr, struct.pack("I", value))
    elif opcode == Ops.MISC:
        # TODO
        pass
    elif opcode == Ops.SYSTEM:
        # I-type instruction
        rd = gibi(11, 7)
        funct3 = Funct3(gibi(14, 12))
        rs1 = gibi(19, 15)
        csr = gibi(31, 20)
        if funct3 == Funct3.CSRRS:
            #print("CSRRS", rd, rs1, csr)
            pass
        elif funct3 == Funct3.CSRRW:
            #print("CSRRW", rd, rs1, csr)
            if csr == 3072:
                return False
        elif funct3 == Funct3.CSRRWI:
            #print("CSRRWI", rd, rs1, csr)
            pass
        elif funct3 == Funct3.ECALL:
            print("ecall", regfile[3])
            if regfile[3] > 1:
                raise Exception("FAILURE IN TEST, PLZ CHECK")
            #return False
        else:
            raise Exception(f"Write more CSR crap: {opcode}/{opcode.value:07b}/{funct3.value:03b}")
    else:
        dump()
        raise Exception(f"Write opcode: {opcode}/{opcode.value:07b}")

    #dump()
    regfile[PC] += 4
    return True
    # Execute
    # Access
    # Write-Back

if __name__ == "__main__":
    xs = [i for i in glob.glob("/home/bensch98/repos/riscv-tests/isa/rv32ui-p-*")]
    xs.sort()
    for x in xs:
        if x.endswith(".dump"):
            continue
        with open(x, 'rb') as f:
            reset()
            print("test", x)
            elf = ELFFile(f)
            for s in elf.iter_segments():
                if s.header.p_type == "PT_LOAD":
                    ws(s.header.p_paddr, s.data())
            regfile[PC] = 0x80000000
            while step():
                pass