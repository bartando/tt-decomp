/**
 * debug_print_nops.cpp — the retail build's debug print
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Every debug print in the shipped game calls 0x8240E6D0, which is a lone
 * `blr`: the printing was compiled out and the calls (and their format
 * strings) were left in. The decompilation calls it by many names; each
 * spelling here does nothing on purpose. The call sites behind each name
 * were checked against the original's `bl 0x8240E6D0`.
 */

#include <cstdint>

// @ 0x8240E6D0 — blr. pong_match.cpp and pong_player.cpp.
void nop_8240E6D0(const char*, ...) {}

// @ 0x8240E6D0 — blr. pong_creature.cpp (pongMover::Reset, the matrix and
// anim-load messages) and pong_ball.cpp.
void rage_DebugLog(const char*, ...) {}
void rage_DebugLog() {}

// @ 0x8240E6D0 — blr. pong_creature.cpp (bone and Teleport messages).
void rage_DebugLogNop(const char*, ...) {}

// @ 0x8240E6D0 — blr. ph_physics.cpp (0x821665B8, 0x82123E78).
void rage_debugLog(const char*, int) {}
void rage_debugLog(const char*, unsigned long long) {}

// The same nop under C linkage. The C-linkage functions sit in a namespace
// so the C++ overloads above can share their names in this file.
namespace c_linkage {
extern "C" {

// @ 0x8240E6D0 — blr. ph_physics.cpp and sg_scene_graph.cpp.
void nop_8240E6D0(const char*, ...) {}

// @ 0x8240E6D0 — blr. char_view.cpp, pong_drill.cpp, rage_par.cpp and
// sysMemSimpleAllocator.cpp (rage_core_utils.cpp's C++ rage_debugLog prints
// on the host; the game doesn't).
void rage_debugLog(const char*, ...) {}

// @ 0x8240E6D0 — blr. rage_audio.cpp (audVoiceSfx's invalid-entry messages).
void audDebugLog(const char*, ...) {}

// @ 0x8240E6D0 — blr, per dialog_validation.cpp's own note on it.
void rage_PrintDebugLine(const char*, ...) {}

}  // extern "C"
}  // namespace c_linkage
