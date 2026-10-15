"""Just enough ELF32 big-endian reading to load a linked lift into the emulator."""
from __future__ import annotations

import struct
from dataclasses import dataclass

SHF_ALLOC = 0x2
SHT_NOBITS = 8


@dataclass
class Section:
    name: str
    addr: int
    size: int
    data: bytes      # zeros for .bss


def load_sections(path: str) -> list[Section]:
    blob = open(path, "rb").read()
    if blob[:4] != b"\x7fELF" or blob[4] != 1 or blob[5] != 2:
        raise ValueError(f"{path}: not a 32-bit big-endian ELF")
    shoff, = struct.unpack_from(">I", blob, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from(">HHH", blob, 0x2E)
    hdrs = [struct.unpack_from(">10I", blob, shoff + k * shentsize) for k in range(shnum)]
    strtab = hdrs[shstrndx]
    names = blob[strtab[4]: strtab[4] + strtab[5]]
    out = []
    for h in hdrs:
        name_off, typ, flags, addr, off, size = h[:6]
        if not flags & SHF_ALLOC or size == 0:
            continue
        name = names[name_off: names.index(b"\0", name_off)].decode()
        data = bytes(size) if typ == SHT_NOBITS else blob[off: off + size]
        out.append(Section(name, addr, size, data))
    return out
