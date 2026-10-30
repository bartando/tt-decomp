# Placeholder global sweep

2026-10-30, starting at `2f1446a` (includes the SWF fix in `bdc23f0`).

**47 candidates found / 46 fixed / 1 unresolved.** Counts refer to the old
placeholder definitions, not the number of replacement externs: some placeholders
conflated several image objects, and the miniheap aggregate contained three words.
The three globals already fixed by `bdc23f0` are excluded from these counts.

## Scope

Reviewed definitions in the 250 C/C++ source and header files under `src/`,
including anonymous-namespace globals, uninitialized statics, function statics,
and the C startup files. Candidates are game state defined in a TU that also
reads/writes it, plus the explicitly guessed physics score constant. Such objects
can survive in a lifted TU instead of resolving against the original image.

Native-only SDL/pthread/TLS bookkeeping, immutable literal copies used by value,
raw address bindings that already access the image, and separate native data
owners are excluded. In particular, the data-only definitions in `*_data.cpp`,
`globals.c`, `rage_globals.cpp`, and the storage blocks in `rage_core_utils.cpp`
are not private copies in their lifted callers. The latter callers already use
externs. The unused voice-manager stub is also excluded.

## Fixed definitions and evidence

- **SWF (4)**, `src/rage/swf.cpp`: `g_currentSwfContext` → `0x8260281C`,
  `g_swfCallDepth` → `0x82604D1C`, `g_swfFrameScale` → `0x82079B90`,
  `g_swfGlobalObject` → `0x82602818`. The slot-13 helper actually uses a separate
  `g_swfSlotObject` at `0x82604848`. Original functions `swfSCRIPTOBJECT_vfn_13`,
  `swfFILE_vfn_10`, `swfSCRIPTOBJECT_vfn_10`, and `swfCONTEXT_B1F0_w` distinguish
  these loads. This corrects the old depth annotation `0x826064EC` and splits the
  two conflicting global-object annotations. Native frame scale is the image's
  `1/1024`, rather than the old placeholder `1`.
- **Asset versions (6)**, `src/game/misc/pong_misc.cpp`: `g_serCtx` →
  `0x825CAF90`; `g_assetVersions_verA`, `g_assetVersionsChar_verA`,
  `g_assetVersionsCS_verA` → `0x825C5864/68/6C`; `g_assetVersions_verB/C` →
  `0x825C803C/38`. The three `assetVersions*::IsSupported` dispatchers load
  these exact slots; field registration loads the shared descriptor slot.
- **Allocator (3)**, `src/rage/memory/sysMemSimpleAllocator.cpp`:
  `g_activeLoggingAllocatorCount` → `0x825EBD20`, `g_sysMemAllocatorInitLock` →
  `0x825EBCF8`, `g_sysMemDebugFillFlag` → `0x8260642D`. Evidence is in
  `sysMemSimpleAllocator_vfn_15/16`, `sysMemSimpleAllocator_vfn_2`, and
  `sysMemSimpleAllocator_62A0_p46`. The flag's old `0x82606315` annotation was wrong.
- **Miniheap (1 aggregate)**, `src/rage/misc/rage_misc.cpp`: replaced
  `g_miniheap` with the actual `start/end/current` words at
  `0x82602808/0C/10`. The original vfn_1/4/5/20 accesses establish both the
  address and field order. Fixed the old `0x82402808` annotation, swapped field
  order, and range check: the upper bound is the current allocation pointer.
- **Input gate (1)**, `src/rage/core/io_input.cpp`: removed the private
  `g_io_input_gate`; `io_9E30` loads the shared `g_loop_obj_ptr` slot at
  `0x825EAB30` (`lis -32161; lwz -21712`).
- **HSM (2)**, `src/rage/core/hsm.cpp`: `lbl_821FA840_a/b` were synthetic nulls.
  `hsmContext_5B40_w`, `hsmContext_5BC8_fw`, and `jumptable_5C20` load their
  name-source/context slots from `0x8271A7C4/C0` (`lis -32142`). Wiring the
  real objects also required restoring their actual access offsets: mode comes
  from the argument, context fields are relative to the singleton itself, the
  name destination is `+4996`, the secondary flag is `+5304`, and the final
  argument-relative store is at `0x127EC`. All three callers are checked.
- **Animation event types (3)**, `src/anim/pcr_anim_events.cpp`:
  `g_eventType_Default/FootAudio/Message` → `0x825C9C60`, `0x825C803C`,
  `0x825C8038`, as loaded by `pcrAnimEvent_vfn_20`. Corrected the conflicting
  header annotations and the stale include/namespace declaration needed to
  compile this previously untested TU.
- **Graphics device (1)**, `src/rage/memory.cpp`: `g_grcDevicePtr` →
  `0x8260637C`; the symbol map and existing native `g_large_buffer_ptr` owner
  agree. The lifted TU now declares the slot and the native name aliases it.
- **Lerp queue (1)**, `src/game/pong_lerp_queue.cpp`: `g_pLerpQueue` →
  `0x8271A2EC`, from `pongLerpQueue_7110_w` (`lis -32142; lwz -23828`).
  Native storage aliases the existing `g_pReplayStateData` slot. This TU still
  has a pre-existing missing `game/pong_lerp_queue.hpp` include and is outside
  CMake, so it was not independently compiled; the changed declaration and
  native alias were checked separately.
- **Ambient streaming (1)**, `src/graphics/fx_effects.cpp`: removed
  `RequestStreamSlot`'s private `prevMappedSlot`. `fxAmbient_2B00_h` reads the
  live mapped slot at `0x825EBB84`, writes the request at `0x825EBBDC`, and
  clamps against `0x825C8F54`. Corrected the related annotations and made this
  instance-independent helper static to match its request-in-r3 ABI.
- **Physics score (1)**, `src/physics/ph_physics.cpp`: replaced the explicitly
  guessed `g_phSimulatorInitialWeakestScore = -FLT_MAX` with an extern at
  `0x8202D108`. `phSimulator_FindWeakestInst` loads that address before its
  empty-list check. Native storage aliases the existing float `1.0` there.
- **XAM startup (13)**, `src/xam/static_init.c`: `g_xam_init_flag` →
  `0x8271B2A0`, `g_xam_singleton` → `0x8271A860`, and nodes
  `g_xam_node_1770/F628/F6A0/F718/F790/F808/F880/F8F8/F970/F9E8/0FF0` →
  `0x825D1698/0FF0/1008/1020/1038/1050/1068/1080/1098/10B0/1518`.
  The original `xam_singleton_init_8D60` and all eleven initializers agree with
  the map; each has a differential spec. Native definitions live in `xam_data.cpp`.
- **CRT startup (6)**, `src/crt/startup.c`: `g_single_init_fn` → `0x825B1298`,
  `g_cinit_retval` → `0x825B0A74`, `g_crt_init_critical_section` → `0x825B0A30`,
  `g_crt_init_callback_list` → `0x825B0A4C`, `g_cinit_list_node` → `0x825E6E78`,
  `g_tls_dispatch` → `0x825E6E84`. The startup routines and map establish these
  objects. Shared native definitions retain the list's self-links and `-1` TLS
  sentinel; their types/declarations are in `include/crt/startup_globals.h`.
- **Vibration (2)**, `src/game/data/gd_vib_event.cpp`: replaced the private
  `g_controllerArray` and `g_playerStateArray` with externs for `0x8271A3A8`
  and `0x825EAB28`, plus the controller-index array at `0x8271A31C`.
  `gdVibEvent_vfn_23` loads these three slots directly; the old code subtracted
  SDA offsets from placeholder addresses. Restored the player-ID return value
  and the controller-index lookup so the original delegated call is preserved.
- **Message handler (1)**, `src/game/network/msg_event_handler.cpp`:
  `g_messageEventType` conflated the event filter at `0x825C5800` with the
  handler identity at `0x825C495C`. Split them, using
  `msgEventHandler_vfn_3/20` as evidence. The latter also accepts the two shared
  base tokens at `0x825C803C/38`. The old `0x8271B800` header annotation has no
  supporting map entry.

Native definitions live in existing data owners, outside the lifted code TUs.
Names for shared addresses alias existing storage (serialization descriptor,
base type IDs, controller slots, graphics flags/device, and lerp singleton)
instead of introducing another native copy. The three SWF externs from
`bdc23f0`, plus its root-object extern, also now have sized native storage.

## Unresolved (1)

`src/game/pong_render.cpp`: `s_bucketData[32]` is explicitly described as a
placeholder and passes `&s_bucketData[i]` to the reconstructed bucket `Load`.
No corresponding image object/address is established. The original
`pongDrawBucketManager_Load` uses stack XML scratch and inline bucket setup;
the reconstructed callee's third argument needs tracing before deciding
whether this is shared image state or per-call data. Left unchanged rather
than assigning an arbitrary address.

## Validation and existing limits

- Added 32 `globals_*` differential specs. They seed live image slots with
  nonzero/random values, check pointer identity and writes, and cover branches
  that private null/zero storage previously hid. Delegated callees are modelled
  or stubbed; this is not validation of every body in the affected TUs. All 32
  pass at 200 trials/seed 1 and 2,000 trials/seed 7 (64,000 additional trials).
- Baseline `tools/lift-check/lift-check all`: 320 specs, 319 PASS,
  1 UNSUPPORTED (`ccal_dispatch_color_constants`). That case intentionally
  exercises unimplemented `vupkd3d128`, and is also used by the tool's self-test.
  It makes `all` exit 1 before and after this sweep.
- Final `all`: **352 specs, 351 PASS, the same 1 UNSUPPORTED**. Also checked
  22 address resolutions directly through the tool's symbol resolver and
  inspected native object symbols to confirm the shared aliases have identical
  addresses.
- Native CMake configuration and compilation succeed. A fresh baseline link
  already failed on 753 unresolved symbols. After this sweep it has 749,
  with no newly unresolved symbols; the four resolved names are the SWF
  buffer, root object, global scope, and script-object vtable. Finishing that
  unrelated link repair is outside this sweep.
