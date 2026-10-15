"""Function signatures and type layouts from the lift's DWARF (llvm-dwarfdump text).

Used to decide which registers a call passes (and how wide they are), what the
function under test returns, and how to read a struct a pointer argument points
at (float members compare with tolerance).
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

_DIE = re.compile(r"^0x([0-9a-f]{8}):(\s+)(DW_TAG_\w+|NULL)")
_ATTR = re.compile(r"^\s+(DW_AT_\w+)\s+\((.*)\)\s*$")
_REF = re.compile(r"^0x([0-9a-f]{8})(?:\s+\"(.*)\")?$")


@dataclass
class Die:
    off: int
    tag: str
    depth: int
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    parent: "Die | None" = None

    def ref(self, name):
        v = self.attrs.get(name)
        if v is None:
            return None
        m = _REF.match(v)
        return int(m.group(1), 16) if m else None

    def str(self, name):
        v = self.attrs.get(name)
        if v is None:
            return None
        if v.startswith('("') or v.startswith('"'):
            return v.strip('()"')
        return v

    def int(self, name):
        v = self.attrs.get(name)
        if v is None:
            return None
        v = v.strip("()")
        try:
            return int(v, 0)
        except ValueError:
            m = re.search(r"DW_OP_plus_uconst (0x[0-9a-f]+)", v)
            return int(m.group(1), 16) if m else None


@dataclass
class TypeInfo:
    kind: str          # 'int' | 'float' | 'ptr' | 'struct' | 'void' | 'array'
    size: int
    name: str = ""
    const_pointee: bool = False
    pointee: "TypeInfo | None" = None
    fields: list = field(default_factory=list)   # [(offset, TypeInfo, name)] for struct/array
    signed: bool = False


@dataclass
class Param:
    name: str
    type: TypeInfo


@dataclass
class Signature:
    name: str
    params: list
    ret: TypeInfo


class Dwarf:
    def __init__(self, obj_path: str, dwarfdump: str):
        text = subprocess.run([dwarfdump, "--debug-info", obj_path], capture_output=True,
                              text=True, check=True).stdout
        self.dies: dict[int, Die] = {}
        stack: list[Die] = []
        cur = None
        for line in text.splitlines():
            m = _DIE.match(line)
            if m:
                depth = len(m.group(2))
                tag = m.group(3)
                if tag == "NULL":
                    cur = None
                    continue
                die = Die(int(m.group(1), 16), tag, depth)
                while stack and stack[-1].depth >= depth:
                    stack.pop()
                if stack:
                    die.parent = stack[-1]
                    stack[-1].children.append(die)
                stack.append(die)
                self.dies[die.off] = die
                cur = die
                continue
            if cur is not None:
                am = _ATTR.match(line)
                if am:
                    cur.attrs[am.group(1)] = am.group(2)
        self.by_linkage: dict[str, Die] = {}
        for d in self.dies.values():
            if d.tag == "DW_TAG_subprogram":
                ln = d.str("DW_AT_linkage_name") or d.str("DW_AT_name")
                if ln and (ln not in self.by_linkage or "DW_AT_declaration" in self.by_linkage[ln].attrs):
                    self.by_linkage[ln] = d
        self._types: dict[int, TypeInfo] = {}

    def type_at(self, off: int | None, depth: int = 0) -> TypeInfo:
        if off is None:
            return TypeInfo("void", 0, "void")
        if off in self._types:
            return self._types[off]
        d = self.dies.get(off)
        if d is None or depth > 40:
            return TypeInfo("int", 4, "?")
        tag = d.tag
        if tag in ("DW_TAG_typedef", "DW_TAG_volatile_type", "DW_TAG_restrict_type",
                   "DW_TAG_atomic_type"):
            t = self.type_at(d.ref("DW_AT_type"), depth + 1)
        elif tag == "DW_TAG_const_type":
            t = self.type_at(d.ref("DW_AT_type"), depth + 1)
        elif tag in ("DW_TAG_pointer_type", "DW_TAG_reference_type", "DW_TAG_rvalue_reference_type",
                     "DW_TAG_ptr_to_member_type"):
            inner = d.ref("DW_AT_type")
            const = inner is not None and self.dies.get(inner) is not None and \
                self.dies[inner].tag == "DW_TAG_const_type"
            t = TypeInfo("ptr", 4, d.str("DW_AT_name") or "ptr", const_pointee=const)
            self._types[off] = t
            t.pointee = self.type_at(inner, depth + 1) if inner is not None else TypeInfo("void", 0)
            return t
        elif tag == "DW_TAG_base_type":
            enc = d.attrs.get("DW_AT_encoding", "")
            size = d.int("DW_AT_byte_size") or 4
            kind = "float" if "float" in enc else "int"
            t = TypeInfo(kind, size, d.str("DW_AT_name") or "", signed="signed" in enc and "unsigned" not in enc)
        elif tag == "DW_TAG_enumeration_type":
            t = TypeInfo("int", d.int("DW_AT_byte_size") or 4, d.str("DW_AT_name") or "enum")
        elif tag in ("DW_TAG_structure_type", "DW_TAG_class_type", "DW_TAG_union_type"):
            t = TypeInfo("struct", d.int("DW_AT_byte_size") or 0, d.str("DW_AT_name") or "")
            self._types[off] = t
            for c in d.children:
                if c.tag == "DW_TAG_member" and "DW_AT_external" not in c.attrs \
                        and "DW_AT_declaration" not in c.attrs:
                    loc = c.int("DW_AT_data_member_location") or 0
                    t.fields.append((loc, self.type_at(c.ref("DW_AT_type"), depth + 1),
                                     c.str("DW_AT_name") or "?"))
                elif c.tag == "DW_TAG_inheritance":
                    loc = c.int("DW_AT_data_member_location") or 0
                    t.fields.append((loc, self.type_at(c.ref("DW_AT_type"), depth + 1), "<base>"))
            return t
        elif tag == "DW_TAG_array_type":
            elem = self.type_at(d.ref("DW_AT_type"), depth + 1)
            count = 0
            for c in d.children:
                if c.tag == "DW_TAG_subrange_type":
                    count = c.int("DW_AT_count") or ((c.int("DW_AT_upper_bound") or -1) + 1)
            t = TypeInfo("array", elem.size * count, "array", pointee=elem)
            t.fields = [(k * elem.size, elem, f"[{k}]") for k in range(count)]
        elif tag == "DW_TAG_subroutine_type":
            t = TypeInfo("struct", 0, "fn")
        else:
            t = TypeInfo("int", 4, tag)
        self._types[off] = t
        return t

    def signature(self, linkage: str) -> Signature | None:
        d = self.by_linkage.get(linkage)
        if d is None:
            return None
        spec = d
        for _ in range(3):
            if spec.ref("DW_AT_specification") is not None:
                spec = self.dies[spec.ref("DW_AT_specification")]
            elif spec.ref("DW_AT_abstract_origin") is not None:
                spec = self.dies[spec.ref("DW_AT_abstract_origin")]
            else:
                break
        src = d if any(c.tag == "DW_TAG_formal_parameter" for c in d.children) else spec
        params = []
        for c in src.children:
            if c.tag == "DW_TAG_formal_parameter":
                tref = c.ref("DW_AT_type")
                if tref is None and c.ref("DW_AT_abstract_origin") is not None:
                    tref = self.dies[c.ref("DW_AT_abstract_origin")].ref("DW_AT_type")
                params.append(Param(c.str("DW_AT_name") or ("this" if "DW_AT_artificial" in c.attrs else "?"),
                                    self.type_at(tref)))
        ret = self.type_at(d.ref("DW_AT_type") if d.ref("DW_AT_type") is not None else spec.ref("DW_AT_type"))
        return Signature(linkage, params, ret)

    def struct_named(self, name: str) -> TypeInfo | None:
        """The complete (non-declaration) struct/class with this name."""
        for d in self.dies.values():
            if d.tag in ("DW_TAG_structure_type", "DW_TAG_class_type", "DW_TAG_union_type") \
                    and d.str("DW_AT_name") == name and "DW_AT_declaration" not in d.attrs:
                return self.type_at(d.off)
        return None


def float_offsets(t: TypeInfo, base: int = 0, out: dict | None = None) -> dict:
    """{offset: size} of the float members inside a type (nested structs flattened)."""
    if out is None:
        out = {}
    if t.kind == "float":
        out[base] = t.size
    elif t.kind in ("struct", "array"):
        for off, ft, _ in t.fields:
            float_offsets(ft, base + off, out)
    return out


def field_path(t: TypeInfo | None, off: int) -> str:
    """'position.z' for an offset inside a struct (best effort)."""
    parts = []
    while t is not None and t.kind in ("struct", "array"):
        hit = None
        for fo, ft, name in t.fields:
            if fo <= off < fo + max(ft.size, 1):
                hit = (fo, ft, name)
        if hit is None:
            break
        fo, t, name = hit
        parts.append(name)
        off -= fo
    return ".".join(parts).replace(".[", "[")


def arg_registers(sig: Signature) -> list[tuple[str, TypeInfo]]:
    """Registers the 32-bit SysV ABI (and Xenon, for these types) uses for each parameter."""
    gpr, fpr, out = 3, 1, []
    if sig.ret.kind in ("struct", "array") and sig.ret.size:
        gpr = 4                             # hidden return-buffer pointer in r3
    for p in sig.params:
        t = p.type
        if t.kind == "float":
            if fpr <= 8:
                out.append((f"f{fpr}", t))
            fpr += 1
        elif t.kind == "int" and t.size == 8:
            if gpr % 2 == 0:
                gpr += 1
            if gpr <= 9:
                out.append((f"r{gpr}:r{gpr + 1}", t))
            gpr += 2
        else:
            if gpr <= 10:
                out.append((f"r{gpr}", t))
            gpr += 1
    return out

