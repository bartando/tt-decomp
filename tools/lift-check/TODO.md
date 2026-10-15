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
