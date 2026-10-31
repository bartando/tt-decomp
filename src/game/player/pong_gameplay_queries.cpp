#include "pong_gameplay_queries.hpp"

extern void* g_pTableDims; // @ 0x8271A304
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
int io_Input_poll_9D68(void* input); // @ 0x821C9D68

// StartServe's query callback leaves a null output alone. Otherwise the
// input gate must be active and the player's live serve state nonzero.
// @ 0x82198A48 | size: 0x74
void io_8A48(pongPlayer* player, int32_t* answer) {
    if (answer == nullptr) return;
    if (static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr)) == 0) {
        *answer = 0;
        return;
    }
    const auto* bytes = reinterpret_cast<const uint8_t*>(player);
    *answer = *reinterpret_cast<const int32_t*>(bytes + 0x17EC) != 0;
}

// Clip readiness, not a player swing predicate: callers also pass embedded
// animation clips and remote playback state. Both float tests are ordered.
// @ 0x820D6AA0 | size: 0xEC
extern "C" bool pongAnimClip_IsPlaybackReady(void* clip)
{
    const auto* bytes = static_cast<const uint8_t*>(clip);
    const auto* values = static_cast<const float*>(clip);
    const uint8_t flags = bytes[312];
    return values[32] > 0.0f
        && (flags & 1) != 0
        && values[72] >= 0.0f
        && bytes[138] != 0
        && bytes[136] == 0
        && (flags & 4) == 0
        && (flags & 8) == 0;
}

// Axis-aligned court limits for the selected side. Only xyz are written;
// retain the scalar load/store order because outputs may alias the settings.
// @ 0x821C9CD0 | size: 0x94
extern "C" void pongMatchSettings_GetCourtBounds(void* settings, int sideIndex,
                                                void* lower, void* upper)
{
    auto* values = static_cast<float*>(settings);
    auto* lo = static_cast<float*>(lower);
    auto* hi = static_cast<float*>(upper);
    lo[1] = 0.0f;
    hi[1] = 0.0f;
    lo[0] = values[32] * -0.5f;
    hi[0] = values[32] * 0.5f;
    const uint8_t side = static_cast<uint8_t*>(settings)[64 + sideIndex];
    const float halfDepth = static_cast<float*>(g_pTableDims)[6] * 0.5f;
    if (side) {
        const float nearZ = values[34] + halfDepth;
        lo[2] = nearZ;
        hi[2] = values[33] + nearZ;
    } else {
        const float nearZ = -halfDepth - values[34];
        hi[2] = nearZ;
        lo[2] = nearZ - values[33];
    }
}
