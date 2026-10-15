# lift-check

Runs a function's original PowerPC from the game image and its lifted C++ (cross-compiled
for 32-bit big-endian PowerPC) in the same emulator, on the same random inputs, and diffs
what they do: memory written, return value, calls made (target, arguments, and what const
pointer arguments point at), callee-saved registers.

`reverb-poc/` and `tristrip-poc/` are the one-off testers this grew out of.

## Setup (once)

```sh
cd tools/lift-check
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python unicorn
```

Needs Homebrew LLVM (`/opt/homebrew/opt/llvm/bin`: clang, llvm-nm, llvm-dwarfdump,
llvm-cxxfilt, llvm-mc) and `ld.lld`; override with `LIFTCHECK_LLVM` / `LIFTCHECK_LLD`.
The game image is read from `TT_IMAGE`, default
`~/PhpstormProjects/ttrecomp/out/xexdump/default_82000000_00770000.bin`. Never copy it
into the repo.

## Checking a lift

1. Write a spec, `specs/<name>.py`:

   ```python
   from liftcheck.spec import *

   FUNCTION = "StlString::Append"          # the lift, as named in SOURCE (or mangled)
   ADDRESS  = 0x8222D5E8                   # the original
   SOURCE   = "src/rage/io/fiAsciiTokenizer.cpp"

   CALLS = {                               # optional; default for any callee: stub()
       "fiAsciiTokenizer_D588_g": alloc(size_reg="r4"),
       "game_DD78_h": run(),
       "rage_free_00C0": stub(ret="void"),
   }

   def inputs(t):                          # once per trial; t.rng is seeded
       s = t.alloc(0x18, "str")
       t.w32(s + 0x10, s + 3)
       ...
       t.args(r3=s, r4=src, r5=src + n)
   ```

2. Run it from the repo root:

   ```sh
   tools/lift-check/lift-check stl_string_append            # 200 trials, seed 1
   tools/lift-check/lift-check my_spec --trials 2000 --seed 7 --ftol 1e-6
   ```

3. Read the first line. Exit code in brackets.
   - `PASS name: 200 trials` [0]
   - `FAIL name: trial N: <first divergence>` [1], then context: the address and struct
     field, both values, the instruction on each side that wrote it (original with its asm
     line), or the two call traces side by side. Rerun that trial with
     `--only N -v` to dump both sides' calls.
   - `SPEC name: the original faulted ...` [2]: your inputs or CALLS are incomplete (it
     lists the calls made before the fault and what they returned).
   - `UNSUPPORTED name: unsupported: <insn> at <addr>` [3]: the original (or lift) uses
     something the emulator can't run.
   - `BUILD name: ...` [2]: the TU didn't cross-compile, or a symbol the lift calls has no
     original address (add it to `EXTERNS = {"name": 0x82...}` or give it a `// @ 0x` marker).

`tools/lift-check/lift-check selftest` runs Xenia's instruction tests through the
emulator, the example specs, and nine mutated lifts that must all fail (about 40 s).

### Spec reference

- `inputs(t)`: `t.alloc(size, name, fill="random"|"zero"|bytes, ctype="Struct")` reserves
  input memory and returns its address (`ctype` makes that struct's float members compare
  with tolerance and names fields in reports); `t.w8/w16/w32/w64/wf32/wf64(addr, v)`;
  `t.floats(addr, n, lo, hi)`; `t.args(r3=..., f1=...)`; `t.vtable("name")` returns a table
  of fake functions whose calls show up as `name.vfn_<k>`; `t.fake_fn("name")`;
  `t.sym("g_x")`; `t.w32(t.sym("g_x"), v)` patches a global in the image for this trial.
  Unset registers are random; `r1` is a fresh stack, `r13` a zeroed block.
- `CALLS`, keyed by symbol name, address or fake-function name:
  - `stub(ret=None|int|float|"void"|fn(ctx), out={"r4": size}, args=("r3", "f1"),
    deref={"r4": 16})`: record and return. The default returns random r3 and f1, and fills
    non-const pointer arguments that point into the stack (out-params) with random data
    typed from the lift's declaration. `args` overrides which registers are compared,
    `deref` compares what a register points at.
  - `returns(v)`, `alloc(size_reg="r3")` (fresh zeroed heap block), `run()` (execute the
    original callee, on both sides), `model(fn)` (Python; `ctx.r(3)`, `ctx.read/write`,
    `ctx.ret(r3=, f1=)`), `fail()`.
  - memcpy, memmove, memset and strlen are Python models and stay out of the call trace
    (MSVC and clang inline different copies); their effects are in the memory diff.
- `EXTERNS`, `FTOL` (relative float tolerance, default 0), `TRIALS`, `RET` (`"r3"`, `"f1"`,
  `None`; default from the lift's return type), `EXTRA_RANGES` (more code ranges that belong
  to the original function).
- `FP_CONTRACT = "off"` (or `--fp-contract off`): compile the lift without fusing `a*b + c`
  into fmadd. The default, `"on"`, fuses within one expression, which is what MSVC did for
  most of the game (5 specs fail with `off`); use `off` where the asm rounds the product
  first (`fmuls` then `fadds`) instead of raising `FTOL`. Lifts always build with
  `-fno-math-errno`, so `sqrtf` is an `fsqrt`, not a libm call.

## How it works

- **Emulator.** Unicorn 2.1 in 32-bit mode as a G4 (7400). Its PPC64 mode is unusable:
  every 64-bit, FP or vector instruction raises exception 96 there, and on the 970 models
  stores go nowhere. Xenon titles run with MSR[SF]=0 anyway (record forms compare the low
  word), so 32-bit mode is the right model. What the G4 can't do runs in Python
  (`assist.py`, `vmx.py`): 64-bit integer ops (upper GPR halves live in a shadow, which
  the 32-bit ops in the same function keep up to date), fsqrt,
  fcfid/fctid/fctiw, dcbz128, and every vector instruction, AltiVec and VMX128 alike
  (Unicorn doesn't expose vector registers). The image is pre-scanned and only those
  addresses are hooked. A CA bit computed in Python goes in through a 4-instruction
  `mtxer` trampoline, because Unicorn's XER register ignores QEMU's CA.
- **The lift.** The TU is compiled to LLVM IR as is (`-ffreestanding`, `shim/` stands in
  for libc/libstdc++, the repo's `include/` and `src/` on the path). Every other function
  in it that has an original address becomes a declaration, so the lift calls the original
  address and the optimiser can't inline or look into it; then `-O2` codegen for
  `powerpc-unknown-elf` (4-byte pointers, so struct layouts match the game's), and
  `ld.lld --gc-sections` at 0x82800000, right after the image. Symbols are resolved from
  `// @ 0x...` markers in `src/` and `include/` (and the TU itself), then
  `config/434C4803/master_symbol_map.json` (`by_name`), and passed as `--defsym`. A marker
  counts on the declaration or definition it trails (any line of a multi-line one), from a
  comment block directly above one (no blank line between), or as `Name @ 0x...` in a
  comment. Where a name has several addresses, one on the declaration itself beats
  comment ones; a call statement's trailing marker counts least. A free function declared
  inside `namespace rage {}` matches `rage::X`; lambdas never resolve. A BUILD error lists
  each unresolved symbol with its conflicting markers. A separate `-O1 -g` object
  supplies the signatures (which registers a call passes and how wide) and struct layouts.
- **Calls.** A block hook catches every jump out of the function (the original's range from
  the symbol map; the lift's own code). The save/restore helpers just run. Both sides get
  the same scripted or random return for the n-th call to a target, and the same clobbered
  volatile registers.
- **Comparison.** Bytes written outside the stack, with floats in `ctype`/`wf32` words and
  float arguments compared to `FTOL` relative to max(1, |a|, |b|); ints exactly. Pointer
  arguments into the stack compare as `<stack>`, plus the pointee if it's `const`; string
  pointers compare by content.

## Limits

- **VMX128 D3D packing** (`vpkd3d128`, `vupkd3d128`) and AltiVec ops outside the common set
  (vmsum*, vmul*, vsum*, pixel packs) report `unsupported`.
- **Estimates aren't Xenon's**: vrefp, vrsqrtefp, vexptefp and vlogefp give the true value,
  fres and frsqrte the G4's estimate. Lifts that divide where the original estimates differ
  by a few ulps, hence `FTOL`. The VMX multiply-adds round the product (non-fused), per
  Xenia's tests; scalar fmadd is fused.
- **Upper GPR halves**: in a function (or `run()` callee, `EXTRA_RANGES`) that has any
  64-bit integer instruction, every native 32-bit instruction that writes a GPR gets its
  64-bit result tracked too (`mulld` + `add` carries, `lwz` zero-extends). Elsewhere a
  native result reads as the sign extension of its low word. Record forms and CA use the
  low word, as with MSR[SF]=0.
- **Headers that don't cross-compile**: 125 of the 157 TUs in `src/` build. The rest have
  errors of their own (missing headers, declarations that don't match) or are the host
  layer (`src/xam`, `src/crt`: SDL, pthread, sockets). `shim/` covers the libc/libstdc++
  subset the sources use; extend it rather than the sources. Patches (`Options.patches`,
  the self-test) apply to the TU only, so a mutated struct has to be defined in the .cpp.
- **ABI**: SysV ppc32 and Xenon agree for ints, pointers and floats in registers. Structs by
  value, 64-bit ints in register pairs (compared, but stubs only return them in r3) and
  varargs aren't modelled.
- **Data the lift defines** (a global with an `// @` address) is the lift's own copy, not the
  image's. Writes to it show up as divergences.
- **Callee signatures** come from the lift; an indirect call through a fake vtable compares
  only r3 unless a `stub(args=...)` says more. Calls without a declaration compare r3 only.
- The `.text.s` disassembly mangles VMX128 (`lvx128 v10,r0,r8` at 0x82193514 shows as
  `vmaddfp128 v10, v0, v8, v3`); lift-check names VMX128 words itself in its reports.

## Findings so far

- `pongPlayer_TossServeBall` (0x821934A0) fails: the lift computes the impulse's w lane
  as `(hit.w - pos.w) / t * mass`, but the asm's reciprocal comes from the `(1, 1, 1, 0)`
  constant at 0x825CB7C0, so the original's w lane is 0. With `velocity._pad = 0.0f` it
  passes 200 trials (the self-test checks both).
