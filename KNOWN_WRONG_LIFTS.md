# Known wrong lifts and misnames

Found by lifting passes (2026-10-15) while working nearby, not fixed yet. Check the asm
before relying on any of these; fix and delete the entry when done.

## Systemic: explicit vtable member + C++ virtuals

Structs that declare a `void** vtable` / `m_vtable` field AND C++ `virtual` methods get a
hidden vptr in front, so every field sits one pointer late (4 bytes on the game's 32-bit
layout). The sweep (2026-10-15) fixed every such struct in the built TUs: keep the explicit
vtable member, make the methods non-virtual, dispatch through the game's slot numbers, and
pin offsets with `static_assert`s that only apply when pointers are 4 bytes. Still mixed:
`rage_audio.hpp` (21 fields wrong without the virtuals; `pong_audio*.cpp` uses them),
`include/rage/swf.hpp` (uses `override`), `rage_sn.hpp`, `pong_hud.hpp`, both `pong_game.hpp`,
`pong_misc.hpp`'s own `pongPlayer` (clashes with the real one), `CCalMoviePlayer`,
`LoopObject`, and headers no built file includes (`fx_effects.hpp`, `rage_swf.hpp`,
`rage_fi.hpp`, `rage_mf.hpp`, `rage_at.hpp`, `include/rage/rage_misc.hpp`,
`pcr_anim_events.hpp`, `gd_cutscene.hpp`). The `grmShaderFx` lifts in `rage_grm.cpp` use raw
offsets and have no specs.

## Systemic: C++ virtual slot numbers don't match the game's vtables

Headers declare virtuals with gaps (Itanium's two destructor slots, undeclared slots), so a
C++ virtual call lands in the wrong slot. Found in `pongPlayer` (slot 9 called as 5),
`pongCreatureInst` (slots 47/48/53/10 called as 26/27/28/8) and `pongTrainingDrill` (every
slot 1..25 one off; fixed, subclasses verified). Lifted code calls through `VCALL` with the
game's slot number where verified; other virtual calls are suspect. Still C++-virtual with
unchecked slot numbers: `CCalMoviePlayer`, `pongSaveFile`, `pongAudioManager`, and
`include/rage/hsmState.hpp` (hsmState's C++ order doesn't match the game's vtable at
0x8206E70C).

## Link blockers (from the link pass, 2026-10-15)

- Data still undefined: `g_sdaBase` is r13+0 (the thread block), so its lift has to change;
  `g_phJoint3DofTemplate` is the element constructor at 0x8225E3F0, a function. About 17
  function addresses are taken as data (`cmSampleCamActions_*`, `CCalMoviePlayer_*_p33`,
  `phDemoWorld_F120`, `fiAsciiTokenizer_8F28_2h`).
- `rage_atStringCopy` (0x82228990) forwards to the unlifted `CopyNetworkString`; the real
  function looks a key up in the string table (0x82408F08) and writes the entry as UTF-8.
- Placeholder bodies that callers rely on (not bridged): `at_types.cpp` `atSingleton_*`,
  `datResource_Load` (912 bytes, a dozen callees), `atHashMap_Clear` (empty);
  `fiAsciiTokenizer.cpp` `ReadBool`/`ReadToken`; `kernel_shims.c` `ke_*Object*`; `hsm.cpp`
  `hsmContext_Init*` (`hsmContext_Init` reads the time base, so lift-check can't compare it),
  `SetTrainingState` (0x821EE9F8 runs per player, not as one state set); `par_xml_types.cpp`
  `xml*` (the originals are virtual calls on a tokenizer); `rage_core_utils.cpp`
  `RtlEnterCriticalSection_D6F0_fw`, `rage::g_capsuleVolK*`/`g_ph*` (guessed values).
- `RegisterSerializationField` (0x821A8F58, ~860 call sites) reads through `g_sda_base`; nothing
  sets that yet, so it crashes at runtime until something does.
- Signatures that really conflict across files: `_locale_register`/`XMemFree` 0x820C02D0 (four
  spellings); `msg_msg_sink.cpp` declares 3E68/3EA8, D168/D1D8, 6220, 5098, A970, E860, EC28,
  DC40, 7970, `game_8CF8_h`, `RtlEnterCriticalSection_A158_h` two ways each;
  `atSingleton_89F8_2hr` (pointer as u32); inside `ph_physics.cpp` `grc_2CC8`, `ph_1B78`,
  `phJoint3Dof_0170_g` (declared with count and constructor swapped; every call passes ptr,
  stride, count, ctor; 17 undefined references), `ph_TokenizerReadInt`; `pongMover_Reset`, `pongPlayer_B208_g`,
  `pongBallInstance_4980_g`, `pg_E6E0`, `LocomotionStateAnim_ApplyAnimData`,
  `ReleaseSingleton`, `rage_strDuplicate`, `rage_7630`, `util_1568`, `xe_GetLoadContext`.
- The `pg_6F48`/`6C40`/`6F10`/`B850`/`C3B8` group are Xbox thread/event wrappers (ResumeThread,
  SetEvent, CloseHandle, SuspendThread, WaitForSingleObject); they need a per-thread
  last-error and a kernel layer the port doesn't have.
- Bridges that forward to ported bodies, not lifts: `rage_free` → `free()`, `xe_EC88` → host
  malloc, `util_PackColorRGBA`, `fiAsciiTokenizer_Destroy` → host `free()` (0x82433310 is the
  CRT's free; unverifiable). Verified forwards: `hsmEvent_Init` → `snEvent_Construct`,
  `netStream_ReadS16` → `datBitBuffer` `ReadSigned<s16>`.

## Wrong lifts

- `fiAsciiTokenizer_CC50_g` returns `void`; the original returns `this`.
- 0x82460718 is lifted twice: `ph_vt57D8_20_Constructor` (`ph_physics.cpp`, unused) and
  `ph_vt57D8_20_0718` (`ph_update_object.cpp`, wrong vtable constants). It is an XAudio
  scalar deleting destructor, not a constructor.
- `msgMsgSink::vfn_126` (0x8244FF38, `msg_msg_sink.cpp`): same name lookup as
  `xactGlobalSettings::FindCategory`, but loses the name argument and treats chain indices
  as pointers.

- 0x82134408 (`xe_buffers.c`, `AllocateU32AlignedWithCounter`, stores a pointer as `uint32_t`)
  and 0x821350B8 (`memory.cpp`, `datPtrArray_DestroyAll`) are the strip list's constructor and
  destructor under unrelated names.
- `pongCameraMgr_6280_g` treats a `grcViewport` as a `pongCameraMgr`.
- `camViewCS` slot 9 is named `OnSourceChanged`, but `pongCameraMgr::Update` calls it every frame.
- 0x82228EA0 reads gameLoop+0x204, which `game_loop_types.h` calls a target FPS; the result is
  an aspect ratio, so one of the two labels is wrong.
- `snJoinMachine.cpp` (not built) calls `rage::hsmState_AttachChild` as
  `snHsmState_AttachChild(void*, void*)`; the real one takes `(hsmStateBase*, hsmStateBase*)`.
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
- `gd_data.cpp` passes XML field types by value (asm: by address); 0x825CAF90 is the Int
  handler, not an enum one.
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
- 0x8222CFA8 (`fiAsciiTokenizer_SetString`) returns `this` in r3; the lift returns void
  (`rage_par.cpp` declares SetString void).
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
- `pong_strings.hpp`: `g_str_pongDrill_tooManySuccesses` is at 0x82031970, not 0x82033970.
- `network.cpp`: 0x822FA818/0x822FA878/0x822FA8F0 are hudTrainingHUD setters ("completed",
  "time_low", "arrow_direction"), not SinglesNetworkClient; 0x822FA8F0 has two names.
- `ph_physics`: 0x82431910 `RoundToNearestInt` is floor; 0x824321F0 is ceil.
- `pong_player_swing.cpp`: 0x821C9CD0 "GetCreatureBoneMatrix" returns one side's play-area
  bounds (leaf, keeps r3).
- `pong_match.hpp`: gmPracticeTarget +0x17 (`field_17`) is a keep-on-table clamp flag.
- `pong_states.cpp` puts string-address `// @` markers on `rage_debugLog` calls.
- 0x8225E998 (`atSingleton_E998_g`, "NotifyObservers") is a variadic message-argument reader
  driven by a format string.
- `fx_effects.hpp`: `fxBallTrail::AddSample` (slot 4) takes r4 and r5, declared with one arg.
- `pong_ball.cpp`: `pongBallInstance_4980_g` is two no-op overloads; the real one takes six
  args (r3–r8). 0x8227FDB0 has two names (`UpdatePhysicsState`, `pongBallInstance_OnBallMissed`).
- `CheckButtonPressed` is commented as 0x8225FFF8; it's 0x821DFFF8.
- `include/game/pong_network_io.hpp` gives `BeginNetworkWrite` as "0x822288AE0" (0x82238AE0).
- `rage_grm.cpp` declares `rage_free_00C0(uint32_t)` (truncates host pointers).
- `ClampMovementToCourtBounds` (0x8219D558): the original stores 0 when the positive overshoot
  is negative and clamps the negative side to -5.0 (0x82079CF0); the lift does neither.
- `UpdateShotTarget` (0x82195D50) drops the r4 matrix argument.
- `xam_utils.c` `RegisterStaticInit_*` comments point at 0x8256B9xx; the functions are at
  0x8257B940..BA40, and the "static init nodes" are command-line option records (netassets,
  path, fast, …).
- `xe_0780` puts the "int" string at 0x8202F5B8 into +0xC, not the grmModelFactory vtable.
- Lifts that store host pointers as `uint32_t`: `*g_globalCamPtr1` (pong_camera vfn_25),
  `g_kGeomOffset`, `g_playerManagerPtr`, `g_swfCMD_globalState` (a `void*` list head; the
  32-bit store clears half of it), and `xe_buffers.c`'s vtable loads.
- `pongAttractState` is defined in both `char_view.cpp` and `pong_attract_state_shims.cpp`.
- 0x825EB988 has five names; 0x825CAEB8 (sysTimeManager) is split across four files with
  different layouts. `g_defaultDuration` and `g_zeroFloat` are each declared at two addresses.
- `pong_creature.cpp:242` dereferences the raw address `(float*)0x82606750`.
- `g_phRandomSeedPtr`/`ActiveCameraPtr`/`GlobalStatePtr` are dereferenced once too often;
  `ph_0CC0`'s state stride is 5, not 3.
- `sysMemAllocator_InitThreadHeap` is 0x820C0038, and its heap is 0x02C00000.
- `gmLogicSpectator_vfn_18` (`pong_match.cpp`) drops a `lis 1` (offset 0x18DA0).
- `char_view.cpp` `PurgeFilteredNodes` is 0x82163D88, not 0x8216DB88.
- The audVoiceStream vtable names are swapped.
- `ph_ctor_0460_Destructor` stores vtable 0x820014C8; the asm stores 0x82059FA8.
- `ph_physics.hpp`: the phBoundCapsule/phInst/phArticulatedCollider/phJoint3Dof/phBoundGeometry
  "+0x" annotations overlap; they're access maps, not layouts. Lifts reading them by name are
  suspect.
- `pongDrawBucket_AddEntry` 0x822278D8 is declared `extern "C"` in `sg_physical.cpp` and with
  C++ linkage in `ph_update_object.cpp`.
- `fragDrawable::ProcessGeometry` 0x820F1C00 is really grmModel's draw (its only caller is
  rmcDrawable at 0x8225D9E4).
- phUpdateObject slot 1 still has a FIXME body.
- `msgMsgSink_84C0_gen` is fixed but unverified: lift-check can't run `mtmsrd`.
- `gd_data_strings.hpp`: the `g_str_*` are probably arrays declared as pointers at wrong
  addresses (`g_str_gdTier_unknownNodeType` was; it's the string at 0x82042844).
- `_crt_tls_fiber_setup` (0x82566B78) is GetCurrentThreadId.
- `sysMemAllocator_Free` is marked with two addresses (0x82186228, 0x820C00C0);
  `rage::ReleaseSingleton` resolves to 0x8204E6FC.
- `~pongNetMessageHolder` stores no vtables and doesn't free.
- `globals.c`: `g_drillCleanupParam` (0x825C74FC) is gdDrillSoftShotData's class id.
- `pong_states.hpp` and `char_view.hpp` both define `pongAttractState`; `pong_camera.hpp` and
  `char_view.hpp` both define `charViewCS`. 0x8216DBB8 is lifted twice
  (`charViewCS::RegisterXmlFields` in `char_view.cpp` is the wrong copy).
- `pongHairData_7B60_g` takes 6 args (r3..r8); `fx_effects.cpp` declares 7.
- `pong_creature.cpp`'s `field_0x` lifts now read the right offsets, but most look invented and
  are unverified.
- `ph_TokenizerReadInt`/`ReadFloat` (0x82430E88/E90) are CRT math wrappers taking a double in f1.
- `math_Sqrt`, `Acos`, `Asin`, `Atan2`, `Sin` are labelled with mid-function addresses
  (0x8240D888…).
- `render_loop.c` `gameLoop_StepFrame` passes `g_pGmLogic`; it should pass the game loop.
- `msg_msg_sink.cpp` thunks 0x8244EFE8/0x824514E8 drop r4 on the way into `rage_C1A8`.
- `gd_data.cpp` lifts 0x821A8F58 wrong as `RegisterSerializedField`; delete it
  (`RegisterSerializationField` in `par_xml_types.cpp` is the verified one).
- `globals.c` defines 0x82619BE0 as all-ones; `pong_creature.cpp` says it keeps xyz only. A
  static initializer sets it, so unverified.
- 0x8271A2F8 +0x10/+0x14 are two `gdBallPredictData*`, swapped per shot by 0x82282A50.
- 0x821CD0F8 (`util_D0F8`) records a replay ball sample into a 900-entry ring; 0x8225FFF8
  invokes a 16-byte functor.
- Symbol-map misnames around the ball: `phBoundCapsule_32D0_g`/`30E0_w` are the ball's flight
  acceleration and bounce (`ball_flight.cpp`); `phBoundCapsule_8368_g` (0x82288368) is the
  predictor's step; `pongBallInstance_1FA0`/`2B08`/`2E18` are phSimulator collision broadphase;
  `pongBallInstance_4E10`/`51B8`/`5400` sit inside RAGE's contact solver;
  `fiAsciiTokenizer_2628_g` (0x82432628) is CRT math, probably `tan`.
- `pong_ball.cpp` `ProcessCollisionAndActivate` (0x8227FA48) is fabricated: the real function
  classifies the impact (0x82280070), posts messages and plays audio, and never touches
  velocity. The `pongBallInstance` fields at +0x42A0 and up are reads of the impact object.
- `pong_player.cpp` `pongShotRecord` is `pongBallHitData`: +0x8C Elasticity,
  +0x90 ExtraCornerBounceAngle, +0x94 Gravity, +0x9C SwingType, +0x40 SpinAxis,
  +0xA0/+0xB0 ServeHitVel/ServeHitAngVel.
- `phArchetypePhys`: +0x1C mass, +0x20 inverse mass, +0x24 gravity factor (slot 12 gets it,
  slot 15 sets it). `phCollider` slot 22 applies gravity, slot 23 damps motion, slot 32
  applies force (+0x120).
- `pong_match.cpp` calls an undefined `BallPredictData_Reset`; it's `gdBallPredictData::Reset`
  (0x821D7750, lifted in `ball_predict.cpp`).


## The recomp is not ground truth

`recomp/structured_pass5_final` has codegen bugs (dropped `li`, reordered checks, wrong
register tested, no stack frames; it drops the `cmpwi r11,10; bne` at 0x822833C4, which
makes the ball's 0.011 drag look like it applies to every swing type but 8 and 9). Trust `disasm/sections/.text.s` when they disagree; see
`tools/lift-check/tristrip-poc/README.md`. Except for VMX128: `.text.s` mangles it
(`lvx128 v10,r0,r8` at 0x82193514 reads `vmaddfp128 v10, v0, v8, v3`), and the recomp's
comments name those instructions right.

## Disassembly caveat

`disasm/sections/.text.s` mis-decodes some AltiVec loads as `vmaddfp128`; cross-check those
against the recomp or the raw bytes in the game image.

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
