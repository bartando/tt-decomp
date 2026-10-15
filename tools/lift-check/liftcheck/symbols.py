"""Names to original addresses: the master symbol map plus `// @ 0x...` markers in src/."""
from __future__ import annotations

import json
import re
from functools import cached_property
from pathlib import Path

_MARKER = re.compile(r"@\s*0x([0-9A-Fa-f]{8})")
_IDENT_CALL = re.compile(r"([A-Za-z_~][\w:~]*)\s*\(")
_QUALIFIED = re.compile(r"\b([A-Za-z_]\w*(?:::[A-Za-z_~]\w*)+)")
_STRUCT = re.compile(r"^\s*(?:struct|class|union)\s+(?:alignas\([^)]*\)\s*)?([A-Za-z_]\w*)\b[^;]*$")
_ADDR_SUFFIX = re.compile(r"(?:^|_)([0-9A-Fa-f]{8})$")
_KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "static_assert", "offsetof",
             "alignas", "decltype", "defined"}


def base_name(demangled: str) -> str:
    """'rage::Foo::Bar(int) const' -> 'rage::Foo::Bar'."""
    depth = 0
    for k, ch in enumerate(demangled):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif ch == "(" and depth == 0:
            return demangled[:k].strip()
    return demangled.strip()


class Symbols:
    def __init__(self, repo: Path):
        self.repo = repo
        data = json.loads((repo / "config/434C4803/master_symbol_map.json").read_text())
        self.by_name: dict[str, int] = {k: int(v, 16) for k, v in data["by_name"].items()}
        self.by_addr: dict[int, dict] = {int(k, 16): v for k, v in data["by_address"].items()}

    def name_at(self, addr: int) -> str | None:
        e = self.by_addr.get(addr)
        return e["name"] if e else None

    def describe(self, addr: int) -> str:
        n = self.name_at(addr)
        return f"0x{addr:08X} {n}" if n else f"0x{addr:08X}"

    def func_range(self, addr: int) -> tuple[int, int] | None:
        e = self.by_addr.get(addr)
        if e and e.get("type") == "function" and e.get("size"):
            return addr, addr + int(e["size"])
        return None

    def helper_ranges(self) -> list[tuple[int, int]]:
        """__savegprlr/__restgprlr/__savefpr/... : code the prologues branch into."""
        out = []
        for n in ("__savegprlr", "__restgprlr", "__savefpr", "__restfpr", "__savevmx", "__restvmx"):
            a = self.by_name.get(n)
            if a is not None:
                r = self.func_range(a)
                if r:
                    out.append(r)
        return out

    # ── `// @ 0x...` markers ───────────────────────────────────────────────
    @cached_property
    def markers(self) -> dict[str, set[int]]:
        index: dict[str, set[int]] = {}

        def add(name, addr):
            name = name.strip(":")
            if not name or name.split("::")[-1] in _KEYWORDS:
                return
            index.setdefault(name, set()).add(addr)

        for path in list((self.repo / "src").rglob("*")) + list((self.repo / "include").rglob("*")):
            if path.suffix not in (".cpp", ".hpp", ".h", ".c", ".inc"):
                continue
            try:
                lines = path.read_text(errors="replace").splitlines()
            except OSError:
                continue
            for n, line in enumerate(lines):
                m = _MARKER.search(line)
                if not m:
                    continue
                addr = int(m.group(1), 16)
                code, _, comment = line.partition("//")
                if code.strip() and "@" not in code:
                    self._index_declaration(code, lines, n, addr, add)
                    continue
                for q in _QUALIFIED.findall(line):
                    add(q, addr)
                head = line[: m.start()]
                for c in _IDENT_CALL.findall(head):
                    add(c, addr)
                for w in re.findall(r"[A-Za-z_]\w*", head)[-1:]:
                    add(w, addr)
                # the definition this comment block sits on
                for k in range(n + 1, min(n + 25, len(lines))):
                    nxt = lines[k].strip()
                    if not nxt or nxt.startswith(("//", "*", "/*")):
                        continue
                    if nxt.startswith(("#", "extern \"C\"")) or nxt == "{":
                        continue
                    cm = _IDENT_CALL.search(nxt)
                    if cm and not nxt.rstrip().endswith(";"):
                        add(cm.group(1), addr)
                    break
        return index

    @staticmethod
    def _index_declaration(code, lines, n, addr, add):
        cm = _IDENT_CALL.search(code)
        if cm:
            name = cm.group(1)
        else:
            vm = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=[^;]*)?;", code)
            if not vm:
                return
            name = vm.group(1)
        add(name, addr)
        if "::" in name:
            return
        # qualify with the enclosing struct, if the declaration sits in one
        depth = 0
        for k in range(n - 1, max(n - 400, -1), -1):
            ln = lines[k].split("//")[0]
            depth += ln.count("}") - ln.count("{")
            if depth < 0:
                for j in range(k, max(k - 3, -1), -1):
                    sm = _STRUCT.match(lines[j].split("//")[0])
                    if sm:
                        add(f"{sm.group(1)}::{name}", addr)
                        return
                return

    def resolve(self, mangled: str, demangled: str) -> int | None:
        """Original address for a symbol the lift references or defines."""
        for cand in (mangled, demangled):
            if cand in self.by_name:
                return self.by_name[cand]
        base = base_name(demangled)
        parts = base.split("::")
        # free function or global: plain name in the map
        if parts[-1] in self.by_name and len(parts) == 1:
            return self.by_name[parts[-1]]
        for k in range(len(parts)):
            q = "::".join(parts[k:])
            hits = self.markers.get(q)
            if hits and len(hits) == 1 and (k < len(parts) - 1 or len(parts) == 1):
                return next(iter(hits))
        if parts[-1] in self.by_name:
            return self.by_name[parts[-1]]
        m = _ADDR_SUFFIX.search(parts[-1])
        if m and parts[-1].startswith(("lbl_", "sub_", "fn_", "func_", "data_", "dword_", "flt_")):
            return int(m.group(1), 16)
        return None
