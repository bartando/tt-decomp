# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- Varargs aren't compared unless named in `args=` (the count isn't known; the format
  string itself compares as text).
- Callees whose call chain goes through a register (vtables, function pointers) are
  clobbered in full; where LTCG keeps registers across one, `preserves=` or `run()`.
- After a `run()` callee has executed once, later calls to the same address aren't in the
  trace, so an extra or missing repeat call that leaves memory unchanged passes
  (`rage_clip_polygon_to_frustum`: dropping the early return after an empty clip).
- A lift that tail-calls a `run()` callee (`return f(x)` compiled to `b`) comes back to
  address 0 and faults; `crt_asin`/`crt_acos` stub the core instead.
- 64-bit arguments need a hand-written register adapter (see README); `t.args` and the
  call comparison could split/join Xenon's single-GPR uint64 themselves.

Reported while the tool was being reworked; recheck against the current version:

- A `// @` marker on `operator=` isn't picked up; the spec needs EXTERNS.
- `t.sym()` reads only the symbol map, not the spec's EXTERNS.
- A CALLS entry keyed by an EXTERNS name is ignored when the symbol map names that address
  differently, so the call gets a random stub.
- A lift that writes outside the input blocks crashes with an unmapped read instead of a FAIL.
