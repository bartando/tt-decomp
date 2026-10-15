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
- `globals.c`: `g_msgSinkTemplate` is at 0x8261A0C0, not 0x8241A0C0.

## Misnamed globals (shared across files, rename together)

| Address | Current name | Really |
|---|---|---|
| 0x8271A318 | `g_pMatchState` | camera shot-manager singleton |
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
