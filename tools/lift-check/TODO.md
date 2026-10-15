# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- The stack fill is set after `inputs()`, so a spec can't see or seed it.
- Varargs aren't compared unless named in `args=` (the count isn't known; the format
  string itself compares as text).
- Non-leaf callees that keep registers (LTCG through a call chain) still need
  `preserves=` or `run()`.
