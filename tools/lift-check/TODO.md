# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- Host-only helpers with no game address (`rage::rage_alloc_aligned`) need a placeholder
  address and a model mirroring the original's inlined code.
- The stack fill is set after `inputs()`, so a spec can't see or seed it.
- Values set by static initializers are zero in the boot image (e.g. 0x82619BD0/BE0).
- Varargs aren't compared unless named in `args=` (the count isn't known; the format
  string itself compares as text).
- Non-leaf callees that keep registers (LTCG through a call chain) still need
  `preserves=` or `run()`.
