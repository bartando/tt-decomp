# lift-check: known tool problems

Reported by the agents using it. Each was worked around in a spec; fix in the tool.

- Symbol resolution: the symbol map wins over `// @` markers for free functions, so a name
  that maps to several addresses resolves to the wrong one (`game_3860` → 0x82483860,
  `game_76A8` → 0x823D76A8) and the lift silently calls the wrong address.
- A marker in a comment above a declaration ending in `;` is never picked up
  (`BallPredictData_Reset`, `gmBallRobot_Update`, `PostPageGroupMessageFmt`, …); the
  comment-to-next-definition rule gave `stateServeBounce_OnEnter` the vtable address
  0x820304FC, making the name ambiguous and failing the build.
- `stub(args=...)` compares `const char*` arguments as pointers, not by content.
- An assertion inside a `model()` prints a Python traceback instead of a FAIL line.
- Varargs need `args` plus a fixed-size `deref` (3 bytes so both "fff" and "ff" compare).
- Host-only helpers with no game address (`rage::rage_alloc_aligned`) need a placeholder
  address and a model mirroring the original's inlined code.
- `model()` has no `args`; indirect calls through the game's own vtables compare r3 by value
  even when it's a stack address.
- A `// @` marker on a function declared unqualified inside `namespace rage {}` never
  resolves for `rage::X`; a same-TU callee then gets inlined into the lift silently.
- `base_name()` cuts a lambda's name at its first `(`, so EXTERNS/markers for the enclosing
  function turn the lambda into a call to that address.
- Const pointees on the stack are compared even for empty structs (one uninitialised byte).
- `stub(args=...)` compares stack pointers raw instead of as `<stack>` and doesn't switch off
  pointee comparison (workaround: `deref={"rN": 0}`).
- Helpers in `specs/` (e.g. `_rage_rsc.py`) start with `_`; anything globbing specs must skip them.
- The marker scan gives a section banner's address to the next code line when that line has
  a trailing `// @` comment.
- `stub()` clobbers r5–r12; leaf callees the original keeps registers across need `run()`.
- No way to ignore an address in the memory diff; the stack fill is set after `inputs()`.
- Clang contracts multiply-adds into FMA where the asm rounds separately (Serve needs FTOL
  1e-5). Compiling lifts with `-ffp-contract=off` should fix it.
- No transparent `run()` for helpers the original inlines (`specs/player_common.py` subclasses it).
