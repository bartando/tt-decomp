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
_NAMESPACE = re.compile(r"\bnamespace\s+([A-Za-z_]\w*)\s*\{")
_NOT_A_TYPE = re.compile(r"[=(){};+\-/%!?.\[\]|^]")
_STATEMENT_WORDS = {"return", "else", "case", "delete", "new", "throw", "goto", "co_return",
                    "co_await", "sizeof", "do"}
_KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "static_assert", "offsetof",
             "alignas", "decltype", "defined", "void", "int", "char", "float", "double", "bool",
             "unsigned", "signed", "short", "long", "const", "auto", "struct", "class", "static",
             "extern", "inline", "virtual", "typedef", "using", "operator", "volatile"}
_FN_POINTER = re.compile(r"\(\s*[*&]\s*([A-Za-z_]\w*)\s*\)\s*\(")


def base_name(demangled: str) -> str | None:
    """'rage::Foo::Bar(int) const' -> 'rage::Foo::Bar', 'void f<int>(int)' -> 'f<int>',
    'void (*f(int))(char)' -> 'f'; None for something local to a function
    ('Foo::Bar(int)::$_0::operator()() const', a lambda)."""
    d = demangled.replace("(anonymous namespace)::", "").strip()
    depth = 0
    for k, ch in enumerate(d):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif ch == "(" and depth == 0:
            if d[k + 1:k + 2] == "*" and k > 0 and d[k - 1] == " ":
                # a function returning a function pointer: R (*name(args))(args)
                inner = base_name(d[k + 2:])
                return inner
            close, pd = k, 0
            for j in range(k, len(d)):
                pd += {"(": 1, ")": -1}.get(d[j], 0)
                if pd == 0:
                    close = j
                    break
            if d[close + 1:].startswith("::"):
                return None
            return _drop_return_type(d[:k].strip())
    return _drop_return_type(d)


def _drop_return_type(name: str) -> str:
    """Template functions demangle with their return type: 'void f<int>' -> 'f<int>'."""
    depth, cut = 0, -1
    for k, ch in enumerate(name):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif ch == " " and depth == 0 and not name[:k].endswith("operator"):
            cut = k
    return name[cut + 1:] if cut >= 0 else name


class Symbols:
    def __init__(self, repo: Path):
        self.repo = repo
        self.extra_files: list[Path] = []
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
    # Each marker is indexed with a strength; resolve() uses the strongest:
    #   2  on the declaration or definition itself (`void F(int);  // @ 0x...`,
    #      also on a later line of a multi-line declaration)
    #   1  a comment block right above a declaration/definition, or `Name @ 0x...`
    #   0  a call statement's trailing marker, a name mentioned elsewhere in the comment
    @cached_property
    def marker_index(self) -> dict[str, dict[int, tuple[int, str]]]:
        """name -> {address: (strength, "file:line")}"""
        index: dict[str, dict[int, tuple[int, str]]] = {}
        self.namespaces: set[str] = set()

        def add(name, addr, strength, where):
            name = name.strip(":")
            if not name or name.split("::")[-1] in _KEYWORDS:
                return
            have = index.setdefault(name, {})
            if addr not in have or have[addr][0] < strength:
                have[addr] = (strength, where)

        paths = list((self.repo / "src").rglob("*")) + list((self.repo / "include").rglob("*"))
        for path in sorted(set(paths) | set(self.extra_files)):
            if path.suffix not in (".cpp", ".hpp", ".h", ".c", ".inc"):
                continue
            try:
                lines = path.read_text(errors="replace").splitlines()
            except OSError:
                continue
            rel = path.relative_to(self.repo) if path.is_relative_to(self.repo) else path
            for n, line in enumerate(lines):
                if "namespace" in line:
                    self.namespaces.update(_NAMESPACE.findall(line))
                m = _MARKER.search(line)
                if not m:
                    continue
                addr = int(m.group(1), 16)
                where = f"{rel}:{n + 1}"
                code, _, comment = line.partition("//")
                if code.strip() and "@" not in code:
                    self._index_declaration(code, lines, n, addr, lambda nm, st: add(nm, addr, st, where))
                    continue
                head = line[: m.start()]
                for q in _QUALIFIED.findall(line):
                    add(q, addr, 1 if q in head else 0, where)
                for c in _IDENT_CALL.findall(head):
                    add(c, addr, 1, where)
                for w in re.findall(r"[A-Za-z_]\w*", head)[-1:]:
                    add(w, addr, 1, where)
                # the declaration or definition this comment block sits on
                for k in range(n + 1, min(n + 25, len(lines))):
                    nxt = lines[k].strip()
                    if not nxt:
                        break                   # a banner or section comment, not a doc block
                    if nxt.startswith(("//", "*", "/*")):
                        continue
                    code = _strip_comment(nxt)
                    if nxt.startswith("#") or code in ("{", 'extern "C"', 'extern "C" {') \
                            or code.startswith("template") and code.endswith(">"):
                        continue
                    if _MARKER.search(nxt):
                        break                   # it has its own
                    if code.endswith(";"):
                        name = self._declared_name(code, lines, k)
                    else:
                        cm = _IDENT_CALL.search(code)
                        name = cm.group(1) if cm else None
                    if name:
                        add(name, addr, 1, f"{rel}:{k + 1}")
                        st = "::" not in name and _enclosing_struct(lines, k)
                        if st:
                            add(f"{st}::{name}", addr, 1, f"{rel}:{k + 1}")
                    break
        return index

    def include(self, path: Path):
        """Also scan `path` for markers (a TU outside src/, e.g. --source)."""
        path = path.resolve()
        if path not in self.extra_files:
            self.extra_files.append(path)
            self.__dict__.pop("marker_index", None)

    @property
    def markers(self) -> dict[str, set[int]]:
        return {k: set(v) for k, v in self.marker_index.items()}

    def _declared_name(self, code, lines, n):
        """The function `code` (line n) declares, or None for a call statement."""
        fp = _FN_POINTER.search(code)
        if fp:
            return fp.group(1)          # a function-pointer variable: R (*name)(args)
        cm = _IDENT_CALL.search(code)
        if not cm:
            return None
        name, prefix = cm.group(1), code[: cm.start()].strip()
        if prefix:
            if _NOT_A_TYPE.search(prefix) or prefix.split()[0] in _STATEMENT_WORDS:
                return None
            return name
        parts = name.split("::")
        if parts[-1].startswith("~") or len(parts) > 1 and parts[-1] == parts[-2]:
            return name
        if len(parts) == 1 and _enclosing_struct(lines, n) in (name, name.lstrip("~")):
            return name
        return None

    def _index_declaration(self, code, lines, n, addr, add):
        """A marker trailing code on line n: a declaration (2) or a call statement (0)."""
        if code.count(")") > code.count("(") and not _IDENT_CALL.search(code):
            # the last line of a multi-line declaration: find the line that opened it
            depth = code.count(")") - code.count("(")
            for j in range(n - 1, max(n - 8, -1), -1):
                prev = _strip_comment(lines[j])
                depth -= prev.count("(") - prev.count(")")
                if depth <= 0:
                    code, n = prev, j
                    break
            else:
                return
        cm = _IDENT_CALL.search(code)
        if cm or _FN_POINTER.search(code):
            name = self._declared_name(code, lines, n)
            if name is None:
                add(cm.group(1), 0)
                return
        else:
            vm = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=[^;]*)?;", code)
            if not vm:
                return
            name = vm.group(1)
        add(name, 2)
        if "::" in name:
            return
        st = _enclosing_struct(lines, n)
        if st:
            add(f"{st}::{name}", 2)

    def explain(self, mangled: str, demangled: str) -> str:
        """Why a name doesn't resolve: its markers, or that it has none."""
        parts = base_name(demangled).split("::")
        for k in range(len(parts)):
            hits = self.marker_index.get("::".join(parts[k:]))
            if hits and len(hits) > 1:
                return "marked at " + ", ".join(f"0x{a:08X} ({w}{', weak' if st < 2 else ''})"
                                                 for a, (st, w) in sorted(hits.items()))
        return "no `// @` marker or symbol-map entry"

    def _marked(self, parts: list[str]) -> int | None:
        for k in range(len(parts)):
            hits = self.marker_index.get("::".join(parts[k:]))
            if not hits:
                continue
            # an unqualified marker stands for X::f only when every X is a namespace
            if k == len(parts) - 1 and k > 0 and not all(p in self.namespaces for p in parts[:k]):
                continue
            top = max(st for st, _ in hits.values())
            best = [a for a, (st, _) in hits.items() if st == top]
            if len(best) == 1:
                return best[0]
        return None

    def resolve(self, mangled: str, demangled: str) -> int | None:
        """Original address for a symbol the lift references or defines. `// @` markers
        beat the symbol map, whose names are often wrong or shared."""
        base = base_name(demangled)
        if base is None:
            return None             # a lambda or other local entity: never an original
        parts = base.split("::")
        a = self._marked(parts)
        if a is not None:
            return a
        for cand in (mangled, demangled):
            if cand in self.by_name:
                return self.by_name[cand]
        if parts[-1] in self.by_name:
            return self.by_name[parts[-1]]
        m = _ADDR_SUFFIX.search(parts[-1])
        if m and parts[-1].startswith(("lbl_", "sub_", "fn_", "func_", "data_", "dword_", "flt_")):
            return int(m.group(1), 16)
        return None


def _strip_comment(line: str) -> str:
    return line.split("//")[0].split("/*")[0].strip()


def _enclosing_struct(lines, n) -> str | None:
    depth = 0
    for k in range(n - 1, max(n - 400, -1), -1):
        ln = lines[k].split("//")[0]
        depth += ln.count("}") - ln.count("{")
        if depth < 0:
            for j in range(k, max(k - 3, -1), -1):
                sm = _STRUCT.match(lines[j].split("//")[0])
                if sm:
                    return sm.group(1)
            return None
    return None
