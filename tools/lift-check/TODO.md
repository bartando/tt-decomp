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
- strcmp isn't modelled; the lift calls the game's (0x82432970) where the original inlines it.
- Calls through a one-branch thunk (`thunk_rage_free` 0x820C0120) count as a different call.
- Stubs clobber f6/f7 too.
- A missing `// @` marker gives a BUILD error with no hint which symbol.
- A name marked with two addresses fails to build.
- Values set by static initializers are zero in the boot image (e.g. 0x82619BD0/BE0).
- Running a callee that calls further functions compares their stack-pointer args raw.
- 64-bit integer ops: `mulld` followed by a plain `add` runs the add as 32-bit, so the carry
  into the upper half is wrong (drill RNG 0x82113BA8 / `OnRallyEnd` 0x8210D660 uncheckable).
- Strings shorter than 2 or longer than ~63 bytes compare as raw pointers; varargs aren't
  compared; a `// @` marker on the second line of a multi-line declaration is missed.
- Link-time codegen keeps registers alive across some calls (`pg_C2A0_g` r8,
  `io_Input_poll_9D68` f1/r7, `pg_0C98_g` r4, trail reset returns `this`); stubs break them.
  A per-callee "preserves" list in the symbol data would let `stub()` keep them.
- clang keeps a libm `sqrtf` call for the errno path; compile lifts with `-fno-math-errno`.
