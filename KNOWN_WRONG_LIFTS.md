# Known wrong lifts and misnames

Found by lifting passes (2026-10-15) while working nearby, not fixed yet. Check the asm
before relying on any of these; fix and delete the entry when done.

## Wrong lifts

- `fiAsciiTokenizer` (`src/rage/io/fiAsciiTokenizer.cpp`) defines a virtual destructor, which
  forces vtable emission; removing it shifts every slot.
- `fiAsciiTokenizer_CC50_g` returns `void`; the original returns `this`.
- `WriteBlockOpen` (`fiAsciiTokenizer.cpp`) loops on `n > 0`; the asm tests `!= 0`.
- 0x82460718 is lifted twice: `ph_vt57D8_20_Constructor` (`ph_physics.cpp`, unused) and
  `ph_vt57D8_20_0718` (`ph_update_object.cpp`, wrong vtable constants). It is an XAudio
  scalar deleting destructor, not a constructor.
- `msgMsgSink_A970_2h` (`pong_network_io.cpp`): the final virtual call should pass
  `this+0xC`; the lift drops it, adds a null check the asm lacks, and calls it a destructor.
- `msgMsgSink_84C0_gen` (`pong_network_io.cpp`): skips the call to 0x82566B78 and does the
  compare-and-swap on `this+0x14` instead of a stack copy of that result. It returns
  0x8AC70012 when the current thread matches the id at `+0x14`.
- `msgMsgSink::vfn_126` (0x8244FF38, `msg_msg_sink.cpp`): same name lookup as
  `xactGlobalSettings::FindCategory`, but loses the name argument and treats chain indices
  as pointers.
- `pongNetMessageHolder::RemoveElementByPointer` (0x82134350, `pong_network.cpp`) compares the
  stored pointer (`*slot == target`); the asm compares the slot address. It is really the
  stripifier's strip-list erase.
- 0x82134408 (`xe_buffers.c`, `AllocateU32AlignedWithCounter`, stores a pointer as `uint32_t`)
  and 0x821350B8 (`memory.cpp`, `datPtrArray_DestroyAll`) are the strip list's constructor and
  destructor under unrelated names.
- `pong_match.hpp`: gmPracticeTarget vtable slot 1 (0x82112DF8) is labelled `ScalarDtor` but is
  the data-file loader; slot 0 (0x82112C70) is the deleting destructor.
- `pongCreatureInst_SetMatrixImpl`, `_NotifyHeadingChanged` and `_ComputeHeading` are
  duplicate wrong lifts of `pongCreatureInst` (fragInst) vtable slots 31, 10 and 9; the
  member versions in `pong_creature.cpp` are the corrected ones.
- `pongCameraMgr_6280_g` treats a `grcViewport` as a `pongCameraMgr`.
- `charViewCS` repeats `camBaseCS`'s fields (CameraFOV/Near/Far at +0xA4..+0xAC) as `m_axisHook*`.
- `camViewCS` slot 9 is named `OnSourceChanged`, but `pongCameraMgr::Update` calls it every frame.
- 0x82228EA0 reads gameLoop+0x204, which `game_loop_types.h` calls a target FPS; the result is
  an aspect ratio, so one of the two labels is wrong.
- 0x82606750 has four names across the codebase (`lbl_82606750` among them).
- `snJoinMachine.cpp` (not built) calls `rage::hsmState_AttachChild` as
  `snHsmState_AttachChild(void*, void*)`; the real one takes `(hsmStateBase*, hsmStateBase*)`.
- `char_view.hpp`: `pongAttractState::OnEnter` (0x82305800) sits in slot 14 but overrides
  `hsmState::OnEnter`, which is slot 5.
- `rage_grm.hpp` still names `grmShader` slot 0 `IsOfType` (asm: scalar deleting destructor)
  and slot 6 `IsOfTypeExt` (asm: stores `this` as the active shader, returns 1).
- `rage_free` (0x820C00C0) is declared `extern "C"` in some files and with C++ linkage in others.
- `globals.c`: `g_msgSinkTemplate` is at 0x8261A0C0, not 0x8241A0C0.

## The recomp is not ground truth

`recomp/structured_pass5_final` has codegen bugs (dropped `li`, reordered checks, wrong
register tested, no stack frames). Trust `disasm/sections/.text.s` when they disagree; see
`tools/lift-check/tristrip-poc/README.md`.

## Misnamed globals (shared across files, rename together)

| Address | Current name | Really |
|---|---|---|
| 0x8271A318 | `g_pMatchState` | `atSingleton<camShotMgr>` instance |
| 0x8271A32C | `g_pMatchConfig` | shared camera state |
| 0x825EBAA0 | `g_pHudOverlay` | current `grcViewport` |

## Not game code

The symbol map files these under game/RAGE class names. They are statically linked
libraries:

| Range | Library | Evidence |
|---|---|---|
| 0x8222C…–0x8222E… | STLport `std::string` / `std::vector` | `"basic_string"` length_error |
| 0x82460…–0x82462C38 (`ph_vt57D8_*`, `phInst_*_p39`) | XAudio (reverb effect) | allocator id 0x82 |
| 0x82484…–0x82493… (`phObject_*`) | XMV movie decoder | allocator id 0x8C, HRESULTs |
| 0x82448…–0x8244F… (`msgMsgSink_*`) | XACT 2 runtime | allocator id 0x84 |
| 0x821342A0–0x821359DC (`cmOperatorCtor_*`) | triangle stripifier (engine tool code, not cm graph) | no vtables; used by 0x82133A28 |
