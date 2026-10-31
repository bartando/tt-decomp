#include <cstdint>

// @ 0x825C9F28 — in-place signal: unused guest vtable pointer, then value.
// The signal is read directly; no virtual operation uses its first word.
extern "C" uint32_t g_selectionKillSignal[2] = {0, 0};
// @ 0x82606327 — cleared/raised during creature mode transitions.
extern "C" uint8_t g_playerModeTransitionFlag = 0;
// @ 0x82606910 — mode-transition basis and translation, assigned at runtime.
extern "C" alignas(16) uint8_t g_playerModeTransform[64] = {};

// @ 0x825EAB48 — per-player mode-animation state, clear at startup.
extern "C" uint8_t g_playerModeAnimationBytes[28] = {};
// @ 0x825CB850 — two vector parameters consumed by the animation pair.
extern "C" alignas(16) const float g_playerModeAnimationPairParams[8] = {0, 0, 0, 1, 0, 0, 0, 0};
