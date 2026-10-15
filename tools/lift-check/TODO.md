# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- `stub(args=...)` compares `const char*` arguments as pointers, not by content.
- An assertion inside a `model()` prints a Python traceback instead of a FAIL line.
- Varargs need `args` plus a fixed-size `deref` (3 bytes so both "fff" and "ff" compare).
- Host-only helpers with no game address (`rage::rage_alloc_aligned`) need a placeholder
  address and a model mirroring the original's inlined code.
- `model()` has no `args`; indirect calls through the game's own vtables compare r3 by value
  even when it's a stack address.
- Const pointees on the stack are compared even for empty structs (one uninitialised byte).
- `stub(args=...)` compares stack pointers raw instead of as `<stack>` and doesn't switch off
  pointee comparison (workaround: `deref={"rN": 0}`).
- `stub()` clobbers r5–r12; leaf callees the original keeps registers across need `run()`.
- No way to ignore an address in the memory diff; the stack fill is set after `inputs()`.
- No transparent `run()` for helpers the original inlines (`specs/player_common.py` subclasses it).
- strcmp isn't modelled; the lift calls the game's (0x82432970) where the original inlines it.
- Calls through a one-branch thunk (`thunk_rage_free` 0x820C0120) count as a different call.
- Stubs clobber f6/f7 too.
- Values set by static initializers are zero in the boot image (e.g. 0x82619BD0/BE0).
- Running a callee that calls further functions compares their stack-pointer args raw.
- Strings shorter than 2 or longer than ~63 bytes compare as raw pointers; varargs aren't
  compared.
- Link-time codegen keeps registers alive across some calls (`pg_C2A0_g` r8,
  `io_Input_poll_9D68` f1/r7, `pg_0C98_g` r4, trail reset returns `this`); stubs break them.
  A per-callee "preserves" list in the symbol data would let `stub()` keep them.
