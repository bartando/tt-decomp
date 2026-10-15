# Lift check: reverb proof of concept

Differential test of the XAudio reverb kernels lifted into `src/physics/ph_physics.cpp`
(0x824621E0–0x82462C38) against the original PowerPC.

- `emu.py` interprets the kernels' instructions straight from `disasm/sections/.text.s`
  (only the opcodes these kernels use), on random filter states and sample buffers.
- `harness.cpp` + `kernels.inc` (the lifted C++, copied out of `ph_physics.cpp`) run the
  same inputs natively; `emu.py` compares state words and buffers.

Result when written: 7 kernels bit-exact, the low-pass within 1.2e-7 (one multiply is
ordered differently in the binary). A deliberately broken lift was caught.

It's a one-off: `HARNESS`/`DATA` in `emu.py` still point at `/tmp/ttd-physics-scripts/`.
Build the harness with `clang++ -std=c++17 -O1 harness.cpp -o /tmp/ttd-physics-scripts/harness`.
The idea worth keeping is the method: a small PPC interpreter turns "reads right against the
asm" into "produces the same bytes as the asm".
