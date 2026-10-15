# Known wrong lifts and misnames

Found by lifting passes (2026-10-15) while working nearby, not fixed yet. Check the asm
before relying on any of these; fix and delete the entry when done.

## Systemic: explicit vtable member + C++ virtuals

Many structs (likely hundreds; `rage_misc.hpp`, `pong_render.hpp`, `char_view.hpp`,
`cm_operators.hpp`, `rage_grm.hpp`, …) declare a `void** vtable` / `m_vtable` field AND C++
`virtual` methods. The compiler then adds its own hidden vptr in front, so every field sits
one pointer late (4 bytes on the game's 32-bit layout). Found by lift-check on `grmModel`
(+0xC read as +0x10), `hsmStateBase`/`hsmState`, `pongPlayer`, the camera classes in `pong_camera.hpp` (all fixed),
and `msgMsgSink` in `pong_misc.hpp` (NOT fixed: ~85 virtuals and the struct is also 4 bytes
short mid-way, so the dialogManager ctor 0x822EC7F8 fails lift-check; spec
`misc_dialog_manager_ctor` documents it). Fix per class: drop one of the
two (keep C++ virtuals only where nothing needs the vtable field by name, otherwise make the
methods non-virtual), then re-verify its lifts.

## Systemic: C++ virtual slot numbers don't match the game's vtables

Headers declare virtuals with gaps (Itanium's two destructor slots, undeclared slots), so a
C++ virtual call lands in the wrong slot. Found in `pongPlayer` (slot 9 called as 5) and
`pongCreatureInst` (slots 47/48/53/10 called as 26/27/28/8). Lifted code calls through
`VCALL` with the game's slot number where verified; other virtual calls are suspect.

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

- 0x82134408 (`xe_buffers.c`, `AllocateU32AlignedWithCounter`, stores a pointer as `uint32_t`)
  and 0x821350B8 (`memory.cpp`, `datPtrArray_DestroyAll`) are the strip list's constructor and
  destructor under unrelated names.
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
- `FinalizeServeSetup` (0x8219F9C0) and `ResetSwingTrackingState` (0x8219FA40) are
  `shotTarget` methods still declared on `pongPlayer`; callers go through a cast.

- `pongPlayer::IsSwingApexReached` / `pongPlayerState::IsSwingApexReached` are another
  duplicate pair at 0x820CDA58, unchecked.
- `pcr_anim_blenders.cpp` declares `pongPlayer_DE98_g` with C++ linkage; it's defined `extern "C"`.
- `pong_player_swing.cpp` (not built) defines `pongPlayer_AB48_g` returning void; it returns
  its first argument.
- `pong_match.cpp` reads `g_render_obj_ptr`'s `+0x1C`/`+0x20` both as player scores and as
  round counts.
- `IsRecovering` uses `<` where the asm tests `!(>= 1.0)` (differs only for NaN).
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
- `gmLogicSinglesMatch_MidGame` "@ 0x8238CA38" is jump-table data, not a function; the lift
  calls vtable slot 0.
- `message.cpp` calls 0x826063AC `g_gameStateMgr`; it's the practice-target set count.
- `message.cpp` (`PostGameEvent`) and `ui_page_group.h` (`ProcessPageGroupInput`) declare
  0x8225E480 wrong; it's a variadic poster driven by a format string ("fff", "ff", …).
- `gd_data.hpp`: `gdaiMeterLogic` slot 21 is named `Validate`; it registers fields.
- `gmLogicSinglesMatch`/`gmLogicSpectator` header skeletons mix an explicit `vtable` member
  with C++ virtuals.
- 0x820F0E78, 0x820F0EE8 (grm ScalarDtors) and 0x8222CFA8 (`fiAsciiTokenizer_SetString`)
  return `this` in r3; the lifts return void (`rage_par.cpp` declares SetString void).
- `grmModelGeom::GetGeometryEntry` reads `this[1]`; probably off by the vtable-member bug.
- `pongPlayer`'s C++ virtuals don't number like the game's vtable (the Itanium destructor
  takes two slots; slots 3–6 and 8 aren't declared), so any virtual call on it through C++
  is suspect; the serve code calls slot 9 through a helper for that reason.
- `cmWorldRefreshableCtor_Destructor` (`cm_operators.cpp:44`) skips the allocator's vtable
  load like `cmOperatorCtor_Allocate` did (fixed there), unverified.
- 0x8214C8F8 (`CopyAnimationData`, fixed in `pong_creature.cpp`) is also lifted as an empty
  no-op in `locomotion.cpp`, and that's the copy callers use.
- `ph_update_object.cpp` marks `g_phFrameIndex` at 0x825C4898; the asm reads 0x826065DC.
- `include/globals.h:119` still mentions `RestorePoseFromRollback` (now `SavePoseSnapshot`).
- 0x820C6378 (`pongCreature` slot 6) still has a TODO body.
- `globals.c`: `g_msgSinkTemplate` is at 0x8261A0C0, not 0x8241A0C0.


## The recomp is not ground truth

`recomp/structured_pass5_final` has codegen bugs (dropped `li`, reordered checks, wrong
register tested, no stack frames). Trust `disasm/sections/.text.s` when they disagree; see
`tools/lift-check/tristrip-poc/README.md`. Except for VMX128: `.text.s` mangles it
(`lvx128 v10,r0,r8` at 0x82193514 reads `vmaddfp128 v10, v0, v8, v3`), and the recomp's
comments name those instructions right.

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
| 0x8202D10C | `g_kZero` (defined 0.0f in `globals.c`) | 0.5 (0.0 is at 0x8202D110) |
| 0x8260633C | `g_swingInFlightFlag` (word) | a byte |

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
