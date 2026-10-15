/**
 * player_state_queries.cpp — pongPlayerState's predicates, by address
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * pong_creature.cpp (and pong_player.cpp for one of them) call these by
 * their map names with C linkage. pong_player.cpp has the same three as
 * pongPlayer methods (IsSwingTimerActive, IsRecovering, IsSwingPhaseBlocked);
 * these follow the asm, NaN cases included.
 */

#include <cstdint>

extern "C" const float g_kFloatConst_D108;   // @ 0x8202D108 (1.0)
extern "C" const float g_kFloatConst_D110;   // @ 0x8202D110 (0.0)

namespace {

struct pongPlayerStateView {
    uint8_t  m_pad00[0x7C];
    uint8_t* m_pSwingTimer;      // +0x7C  elapsed at +0x1C, target at +0x30
    uint8_t* m_pRecovery;        // +0x80  force-block byte at +0x2C, timer at +0xAC
    uint8_t  m_pad84[0x04];
    uint8_t* m_pAnimState;       // +0x88  flags (u16) at +0x5A, phase at +0x19C
};

float F32(const uint8_t* p, uint32_t off) {
    float v;
    __builtin_memcpy(&v, p + off, sizeof v);
    return v;
}

}  // namespace

// @ 0x820CD550 — the swing timer is still running: elapsed hasn't reached
// the target (or either is NaN).
extern "C" bool pongPlayer_D550_g(void* statep) {
    const pongPlayerStateView* state = static_cast<const pongPlayerStateView*>(statep);
    if (state->m_pSwingTimer == nullptr) {
        return false;
    }
    return !(F32(state->m_pSwingTimer, 0x1C) >= F32(state->m_pSwingTimer, 0x30));
}

// @ 0x820CD598 — recovering from a swing: forced, or the recovery timer
// hasn't reached 1.0 (or is NaN).
extern "C" bool pongPlayer_D598_g(void* statep) {
    const pongPlayerStateView* state = static_cast<const pongPlayerStateView*>(statep);
    if (state->m_pRecovery == nullptr) {
        return false;
    }
    if (state->m_pRecovery[0x2C] != 0) {
        return true;
    }
    return !(F32(state->m_pRecovery, 0xAC) >= g_kFloatConst_D108);
}

// @ 0x820CD5F0 — the swing phase is blocked: the anim phase is past 0.0
// (or NaN), or bit 0 of the anim state's flags is set.
extern "C" bool pongPlayer_D5F0_g(void* statep) {
    const pongPlayerStateView* state = static_cast<const pongPlayerStateView*>(statep);
    if (state->m_pAnimState == nullptr) {
        return false;
    }
    const float phase = F32(state->m_pAnimState, 0x19C);
    if (phase > g_kFloatConst_D110 || phase != phase) {
        return true;
    }
    uint16_t flags;
    __builtin_memcpy(&flags, state->m_pAnimState + 0x5A, sizeof flags);
    return (flags & 1) != 0;
}
