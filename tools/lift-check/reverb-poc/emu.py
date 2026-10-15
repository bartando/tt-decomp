"""Tiny PPC interpreter for the reverb kernels; compares against the C++ lift."""
import re, struct, random, subprocess, sys

TEXT = __import__('os').path.join(__import__('os').path.dirname(__file__), '../../../disasm/sections/.text.s')
HARNESS = '/tmp/ttd-physics-scripts/harness'
DATA = '/tmp/ttd-physics-scripts/data.bin'

def load_code(lo, hi):
    code = {}
    pat = re.compile(r'^0x([0-9A-F]{8}):\s+(\S+)\s*(.*)$')
    with open(TEXT) as f:
        for line in f:
            if not line.startswith('0x824'):
                continue
            m = pat.match(line.rstrip())
            if not m:
                continue
            a = int(m.group(1), 16)
            if lo <= a < hi:
                code[a] = (m.group(2), [x.strip() for x in m.group(3).split(',')] if m.group(3) else [])
    return code

def f32(x):
    return struct.unpack('>f', struct.pack('>f', x))[0]

class Mem:
    def __init__(self):
        self.b = {}
    def w32(self, a, v):
        for i, byte in enumerate(struct.pack('>I', v & 0xFFFFFFFF)):
            self.b[a + i] = byte
    def r32(self, a):
        return struct.unpack('>I', bytes(self.b.get(a + i, 0) for i in range(4)))[0]
    def wf(self, a, v):
        self.w32(a, struct.unpack('>I', struct.pack('>f', v))[0])
    def rf(self, a):
        return struct.unpack('>f', struct.pack('>I', self.r32(a)))[0]

def reg(s):
    return int(s[1:])

def imm(s):
    return int(s, 0)

def mask(mb, me):
    m = 0
    for i in range(mb, me + 1):
        m |= 1 << (31 - i)
    return m

def rotl(v, n):
    v &= 0xFFFFFFFF
    return ((v << n) | (v >> (32 - n))) & 0xFFFFFFFF if n else v

def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v

def run(code, pc, mem, r):
    fr = [0.0] * 32
    cr = 0  # -1 lt, 0 eq, 1 gt
    steps = 0
    while True:
        steps += 1
        assert steps < 10_000_000
        op, a = code[pc]
        npc = pc + 4
        if op in ('mflr',):
            pass
        elif op == 'bl':
            t = int(a[0], 16)
            assert 0x8242f800 <= t < 0x8242f900, hex(t)  # savegpr
        elif op == 'b':
            t = int(a[0], 16)
            if 0x8242f800 <= t < 0x8242f900:
                return  # restgpr + return
            npc = t
        elif op == 'blr':
            return
        elif op == 'lis':
            r[reg(a[0])] = (imm(a[1]) << 16) & 0xFFFFFFFF
        elif op == 'li':
            r[reg(a[0])] = imm(a[1]) & 0xFFFFFFFF
        elif op == 'addi':
            base = 0 if a[1] == 'r0' else r[reg(a[1])]
            r[reg(a[0])] = (base + imm(a[2])) & 0xFFFFFFFF
        elif op == 'add':
            r[reg(a[0])] = (r[reg(a[1])] + r[reg(a[2])]) & 0xFFFFFFFF
        elif op == 'subf':
            r[reg(a[0])] = (r[reg(a[2])] - r[reg(a[1])]) & 0xFFFFFFFF
        elif op == 'subfic':
            r[reg(a[0])] = (imm(a[2]) - r[reg(a[1])]) & 0xFFFFFFFF
        elif op == 'neg':
            r[reg(a[0])] = (-r[reg(a[1])]) & 0xFFFFFFFF
        elif op == 'slwi':
            r[reg(a[0])] = (r[reg(a[1])] << imm(a[2])) & 0xFFFFFFFF
        elif op == 'srwi':
            r[reg(a[0])] = r[reg(a[1])] >> imm(a[2])
        elif op == 'clrlwi':
            r[reg(a[0])] = r[reg(a[1])] & (0xFFFFFFFF >> imm(a[2]))
        elif op == 'rlwinm':
            r[reg(a[0])] = rotl(r[reg(a[1])], imm(a[2])) & mask(imm(a[3]), imm(a[4]))
        elif op in ('cmpwi', 'cmplwi', 'cmplw'):
            x = r[reg(a[1])]
            y = imm(a[2]) & 0xFFFFFFFF if op != 'cmplw' else r[reg(a[2])]
            if op == 'cmpwi':
                x, y = s32(x), s32(y)
            cr = (x > y) - (x < y)
        elif op in ('blt', 'bgt', 'bne', 'beq'):
            t = int(a[1], 16)
            take = {'blt': cr < 0, 'bgt': cr > 0, 'bne': cr != 0, 'beq': cr == 0}[op]
            if take:
                npc = t
        elif op in ('lwz', 'stw', 'lfs', 'stfs'):
            m = re.match(r'(-?0x[0-9a-f]+|-?\d+)\((r\d+)\)', a[1])
            ea = (int(m.group(1), 0) + r[reg(m.group(2))]) & 0xFFFFFFFF
            if op == 'lwz':
                r[reg(a[0])] = mem.r32(ea)
            elif op == 'stw':
                mem.w32(ea, r[reg(a[0])])
            elif op == 'lfs':
                fr[reg(a[0])] = mem.rf(ea)
            else:
                mem.wf(ea, fr[reg(a[0])])
        elif op == 'lfsx':
            base = 0 if a[1] == 'r0' else r[reg(a[1])]
            fr[reg(a[0])] = mem.rf((base + r[reg(a[2])]) & 0xFFFFFFFF)
        elif op == 'fmr':
            fr[reg(a[0])] = fr[reg(a[1])]
        elif op == 'fmuls':
            fr[reg(a[0])] = f32(fr[reg(a[1])] * fr[reg(a[2])])
        elif op == 'fsubs':
            fr[reg(a[0])] = f32(fr[reg(a[1])] - fr[reg(a[2])])
        elif op == 'fmadds':
            fr[reg(a[0])] = f32(fr[reg(a[1])] * fr[reg(a[2])] + fr[reg(a[3])])
        else:
            raise NotImplementedError(op)
        pc = npc

# kernel id -> (address, end, kind, length, state size)
KERNELS = {
    0: (0x824621E0, 'lowpass', 0, 0x20),
    1: (0x82462310, 'tap3', 512, 0x82C),
    2: (0x824623E0, 'ap_inplace', 128, 0x218),
    3: (0x82462678, 'tap3', 2048, 0x202C),
    4: (0x82462748, 'ap_inplace', 256, 0x418),
    5: (0x824628B8, 'ap_inplace', 512, 0x818),
    6: (0x82462A28, 'ap_out', 512, 0x818),
    7: (0x82462B90, 'tap2', 1024, 0x1020),
}

STATE, IN, OUTA, OUTB = 0x10000000, 0x20000000, 0x30000000, 0x40000000

def fbits(x):
    return struct.unpack('>I', struct.pack('>f', x))[0]

def make_state(kind, length, size, rng):
    words = [fbits(rng.uniform(-1, 1)) for _ in range(size // 4)]
    def setw(off, v):
        words[off // 4] = v & 0xFFFFFFFF
    def setf(off, v):
        words[off // 4] = fbits(v)
    blocks = max(1, length // 256)
    if kind == 'lowpass':
        setf(0x18, rng.uniform(0.2, 1.5)); setf(0x1C, rng.uniform(0, 0.99))
    elif kind == 'tap3':
        for t in range(3):
            setw(t * 12, rng.randrange(0, length))
        setw(0x24, 256 * rng.randrange(0, blocks))
    elif kind == 'tap2':
        for t in range(2):
            setw(t * 12, rng.randrange(0, length))
        setw(0x18, 256 * rng.randrange(0, blocks))
    else:
        setw(0x00, rng.randrange(0, length))
        setw(0x10, 0 if length <= 256 else 256 * rng.randrange(0, blocks))
    return words

def main():
    rng = random.Random(1234)
    code = load_code(0x824621E0, 0x82462C38)
    worst = {}
    for kid, (addr, kind, length, size) in KERNELS.items():
        for trial in range(4):
            words = make_state(kind, length, size, rng)
            counts = [256, 256, 256] if kind != 'lowpass' else [256, 7, 0, 1, 5, 256]
            for count in counts:
                inbuf = [rng.uniform(-1, 1) for _ in range(260)]
                oa = [rng.uniform(-1, 1) for _ in range(260)]
                ob = [rng.uniform(-1, 1) for _ in range(260)]
                # emulator
                mem = Mem()
                for i, w in enumerate(words):
                    mem.w32(STATE + 4 * i, w)
                for base, buf in ((IN, inbuf), (OUTA, oa), (OUTB, ob)):
                    for i, v in enumerate(buf):
                        mem.wf(base + 4 * i, v)
                mem.wf(0x82003DAC, 1.0)
                r = [0] * 32
                r[1] = 0x70000000
                r[3], r[4], r[5], r[6], r[7] = STATE, IN, OUTA, OUTB, 256
                if kind == 'lowpass':
                    r[5], r[6] = OUTA, count
                elif kind == 'ap_inplace':
                    pass
                elif kind == 'ap_out':
                    r[5] = OUTA
                run(code, addr, mem, r)
                emu_state = [mem.r32(STATE + 4 * i) for i in range(len(words))]
                emu_bufs = [[mem.rf(base + 4 * i) for i in range(260)] for base in (IN, OUTA, OUTB)]
                # C++
                with open(DATA, 'wb') as f:
                    f.write(b''.join(struct.pack('<I', w) for w in words))
                    for buf in (inbuf, oa, ob):
                        f.write(b''.join(struct.pack('<f', v) for v in buf))
                subprocess.run([HARNESS, str(kid), str(size), str(count), DATA], check=True)
                raw = open(DATA, 'rb').read()
                cpp_state = list(struct.unpack('<%dI' % len(words), raw[:size]))
                off = size
                cpp_bufs = []
                for _ in range(3):
                    cpp_bufs.append(list(struct.unpack('<260f', raw[off:off + 1040])))
                    off += 1040
                # compare: ints exactly, floats with tolerance
                err = 0.0
                for i, (e, c) in enumerate(zip(emu_state, cpp_state)):
                    if e == c:
                        continue
                    ef = struct.unpack('>f', struct.pack('>I', e))[0]
                    cf = struct.unpack('>f', struct.pack('>I', c))[0]
                    d = abs(ef - cf)
                    if d > 1e-4 or ef != ef or cf != cf:
                        print('STATE MISMATCH', hex(addr), 'word', hex(4 * i), hex(e), hex(c), ef, cf)
                        sys.exit(1)
                    err = max(err, d)
                for name, eb, cb in zip(('in', 'outA', 'outB'), emu_bufs, cpp_bufs):
                    for i, (e, c) in enumerate(zip(eb, cb)):
                        d = abs(e - c)
                        if d > 1e-4:
                            print('BUFFER MISMATCH', hex(addr), name, i, e, c)
                            sys.exit(1)
                        err = max(err, d)
                words = cpp_state  # carry state into the next block
                worst[hex(addr)] = max(worst.get(hex(addr), 0.0), err)
    for k, v in worst.items():
        print(k, 'ok, max abs diff', v)

main()
