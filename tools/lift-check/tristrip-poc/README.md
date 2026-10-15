# Lift check: triangle stripifier proof of concept

Differential test of the stripifier lifted into `src/game/misc/cm_operators.cpp`
(0x821342A0–0x821359DC; filed in the symbol map as `cmOperatorCtor_*`).

Unlike `../reverb-poc` (an instruction interpreter), this compiles the ReXGlue output from
`recomp/structured_pass5_final` natively: `ppc_shim.h` supplies `PPCContext`, the
`PPC_FUNC_IMPL` macros and big-endian loads/stores over a flat guest memory buffer.
`main.cpp` runs the recomp bodies (`recomp_*.inc`, hand-corrected, see below) and the lift
(`lifted_tu.cpp`) on thousands of random meshes, strip lists and cache states and compares.
All six functions matched exactly; deliberately broken lifts failed.

The recomp is not ground truth. In these functions it was wrong in four places, confirmed
against `disasm/sections/.text.s` and fixed in the `.inc` copies:
- drops `li r9,-1` in 0x82134E90 and 0x82135648;
- in 0x821342A0 it does the size check after the shift instead of before;
- in 0x82134E90 it tests r3 instead of r9 when entering the join loop;
- it never sets up stack frames, so nested calls that use the stack overlap.

Build: `clang++ -std=c++17 -O1 main.cpp -o /tmp/difftest` from this folder.
