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
- `pongPlayer::CancelSwing`, `IsBeforeSwingPeak`, `IsSwingSystemIdle`, `IsInReturnPosition`
  have the swing-timer test inverted (their `pongPlayerState::` duplicates at the same
  addresses are right); `CancelSwing` also writes the wrong constants.
- `SetupRecoverySlots` (0x820C7248): `this` is a `pongCreature`, the two arguments are 16-byte
  callbacks, not `vec3`s; it copies them unconditionally, then passes a position and two bools
  to `game_D060`. Its timer test is inverted too.
- `ComputeShotSpeedForType` (0x821D6100) runs on the per-player shot record, not `pongPlayer`;
  `FinalizeServeSetup` (0x8219F9C0) is a `shotTarget` method.
- `PostPageGroupMessage`: `pg_E6E0` takes 4 arguments, the declaration has 5.
- `pong_player.hpp`: the `pongPlayer` layout below +0x100 is really `pongCreature`'s;
  `m_pOpponent` (+0x1C4) is the player's own creature, `m_pActionState` (+0x1F0) is an
  `aiPlayer`, +0x1C0 is the ball's physics instance.
- `pongBallHitData::LoadProperties` (0x821D6608) uses made-up field names; the real first
  three are `Quality`, `Force`, `HitForce`.
- `gmBallNode::IsEventHandled` (slot 20) is really a type check; its four "ball event hash"
  globals are invented names.
- `fx_effects.hpp` calls fxBallSpinTex slot 1 `ScalarDtor`, but `gmBallNode::Draw` calls it
  every frame.
- `sg_physical.hpp`: `+0x74` is the phInst, `+0x7C` a separate draw object.
- `gd_data.cpp` passes XML field types by value (asm: by address); 0x825CAF90 is the Int
  handler, not an enum one.
- `globals.c` swaps the pointer and type arrays at 0x825F3868/0x825F3968.
- 0x825EBC54 (`boundContext` in `rage_grm.cpp`) behaves like a write counter.
- `fx_effects.cpp` and `ProcessAnimationList` pass the skeleton to 0x8224C128/0x8224C288
  (LocomotionStateAnim C128/C288) in r4; the asm reads it from r5.
- `pongPlayer_B208_g` and `pongPlayer_D7B0_g` are `pongPlayerState` functions.
- `pongMover::Reset` is still broadly wrong (only its teleport call was fixed).
- `ph_physics.cpp` has two conflicting names for 0x820C3F98 (builds a rotation about y).
- 0x8271A2EC/0x8271A2F0 hold replay data in `pong_creature.cpp` but are called "shadow
  table"/"match logic" elsewhere; 0x8271A2F4 is stored as `uint32_t` in `pong_ball`.
- `pongCreature::Reset`, `RegisterShadowCasters`, `RestorePoseFromRollback` look rough and
  were never checked against the asm.
- `globals.c`: `g_msgSinkTemplate` is at 0x8261A0C0, not 0x8241A0C0.

## The recomp is not ground truth

`recomp/structured_pass5_final` has codegen bugs (dropped `li`, reordered checks, wrong
register tested, no stack frames). Trust `disasm/sections/.text.s` when they disagree; see
`tools/lift-check/tristrip-poc/README.md`.

## Disassembly caveat

`disasm/sections/.text.s` mis-decodes some AltiVec loads as `vmaddfp128`; cross-check those
against the recomp or the raw bytes in the game image.

## Misnamed globals (shared across files, rename together)

| Address | Current name | Really |
|---|---|---|
| 0x8271A318 | `g_pMatchState` | `atSingleton<camShotMgr>` instance |
| 0x8271A32C | `g_pMatchConfig` | shared camera state |
| 0x825EBAA0 | `g_pHudOverlay` | current `grcViewport` |
| 0x8271A304 | `g_pGlobalClock` | table dimensions |
| 0x8202D10C | `g_kZero` | 0.5 (0.0 is at 0x8202D110) |

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
