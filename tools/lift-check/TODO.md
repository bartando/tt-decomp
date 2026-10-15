# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- Varargs aren't compared unless named in `args=` (the count isn't known; the format
  string itself compares as text).
- Callees whose call chain goes through a register (vtables, function pointers) are
  clobbered in full; where LTCG keeps registers across one, `preserves=` or `run()`.

Reported while the tool was being reworked; recheck against the current version:

- A `// @` marker on `operator=` isn't picked up; the spec needs EXTERNS.
- `t.sym()` reads only the symbol map, not the spec's EXTERNS.
- A CALLS entry keyed by an EXTERNS name is ignored when the symbol map names that address
  differently, so the call gets a random stub.
- A lift that writes outside the input blocks crashes with an unmapped read instead of a FAIL.
