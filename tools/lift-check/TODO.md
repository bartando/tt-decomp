# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- Varargs aren't compared unless named in `args=` (the count isn't known; the format
  string itself compares as text).
- Callees whose call chain goes through a register (vtables, function pointers) are
  clobbered in full; where LTCG keeps registers across one, `preserves=` or `run()`.
