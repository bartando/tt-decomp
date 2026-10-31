#include "rage/ptr32.hpp"
#include "rage/index_wrap.hpp"
#include "game/camera_queries.hpp"
/**
 * pong_camera_helpers.cpp
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Helper / trampoline functions for pongCameraMgr transitions.
 *
 * These are the C-linkage helpers that pong_camera.cpp uses to implement
 * the clamped-transition family (TryTransition, TryTransitionMode20,
 * the Query* glue, etc.). Previously these lived in src/stubs.cpp as
 * zeroed shims; they are lifted here from the recomp-generated scaffold
 * for each address.
 */

#include <cstdint>
#include <cstring>

#include "pong_camera.hpp"

// .rdata float threshold used by pongCameraMgr_3500_fw / 35A0_fw / 3650_fw.
// Located at 0x825C5EC0 (loaded via `lis r11,-32164 ; lfs f13,24256(r11)`).
extern float g_cameraThreshold;

extern uint8_t pg_ApplyTransition(void* gameState, TransitionParams* params,
                                  int mode, TransitionFlags* flags, int enable);
bool pongCameraMgr_3500_fw(pongCameraMgr* self, void* evaluator, int mode); // @ 0x821F3500

// A transition is an eight-byte key, mode, and a slice of the condition ring.
struct CameraTransitionEntry {
    TransitionParams key;
    int32_t mode;
    int32_t firstCondition;
    int32_t numConditions;
};
static_assert(sizeof(CameraTransitionEntry) == 20, "transition entry stride");

extern "C" void* g_pReplayStateData; // @ 0x8271A2EC

namespace {
struct CameraConditionRing {
    uint8_t unused00[8];
    rage::ptr32<TransitionFlags> entries; // +0x08
    uint32_t unused0C;
    int32_t capacity;                    // +0x10
};
struct CameraTransitionRing {
    uint8_t unused00[8];
    int32_t count;                      // +0x08
    rage::ptr32<CameraTransitionEntry> entries;
    int32_t end;                        // +0x10
    uint32_t unused14;
    int32_t head;                       // +0x18
    int32_t capacity;                   // +0x1C
    int32_t cursor;                     // +0x20
    int32_t cursorCapacity;             // +0x24
};
static_assert(offsetof(CameraConditionRing, capacity) == 0x10, "condition ring layout");
static_assert(offsetof(CameraTransitionRing, capacity) == 0x1C, "transition ring layout");
int32_t ringRemainder(int32_t index, int32_t capacity) {
    if (capacity == 0 || (index == (-2147483647 - 1) && capacity == -1))
        __builtin_trap();
    return index % capacity;
}
int32_t nextRingIndex(int32_t index, int32_t capacity) {
    return ringRemainder(static_cast<int32_t>(static_cast<uint32_t>(index) + 1u), capacity);
}
bool conditionEqual(const TransitionFlags& event, const TransitionFlags& required) {
    if (event.flag1 != required.flag1) return false;
    if (event.flag1 >= 1 && event.flag1 <= 5) return event.flag2 == required.flag2;
    if (event.flag1 != 6) return false;
    float a, b;
    __builtin_memcpy(&a, &event.flag2, sizeof a);
    __builtin_memcpy(&b, &required.flag2, sizeof b);
    return a == b;
}
}

// Advance within an inclusive [head,end] range, which can straddle zero.
// The cursor's following word stores the physical capacity.
// @ 0x82215B10 | size: 0xB8
void pg_5B10_fw(int32_t* cursor, const int32_t* head, const int32_t* end) {
    const int32_t low = *head, high = *end;
    if (static_cast<uint32_t>(high) > static_cast<uint32_t>(low)) {
        *cursor = math_WrapIndex(static_cast<int32_t>(static_cast<uint32_t>(*cursor) + 1u), low, high);
    } else if (static_cast<uint32_t>(high) < static_cast<uint32_t>(low)) {
        if (*cursor >= low) {
            *cursor = static_cast<int32_t>(static_cast<uint32_t>(*cursor) + 1u);
            if (*cursor >= cursor[1]) *cursor = 0;
        } else if (*cursor <= high) {
            *cursor = static_cast<int32_t>(static_cast<uint32_t>(*cursor) + 1u);
            if (*cursor > high) *cursor = low;
        }
    }
}

// @ 0x82215BC8 | size: 0xB8
void pg_5BC8_fw(int32_t* cursor, const int32_t* head, const int32_t* end) {
    const int32_t low = *head, high = *end;
    if (static_cast<uint32_t>(high) > static_cast<uint32_t>(low)) {
        *cursor = math_WrapIndex(static_cast<int32_t>(static_cast<uint32_t>(*cursor) - 1u), low, high);
    } else if (high < low) {
        if (*cursor >= low) {
            *cursor = static_cast<int32_t>(static_cast<uint32_t>(*cursor) - 1u);
            if (*cursor < low) *cursor = high;
        } else if (*cursor <= high) {
            *cursor = static_cast<int32_t>(static_cast<uint32_t>(*cursor) - 1u);
            if (*cursor < 0) *cursor = static_cast<int32_t>(static_cast<uint32_t>(cursor[1]) - 1u);
        }
    }
}

// Every required condition must occur in the entry's event slice. Conditions
// 1..5 compare integer bits; condition 6 compares float values (including NaNs).
// @ 0x82215CE8 | size: 0x120
uint8_t pongCameraMgr_5CE8(const CameraTransitionEntry* entry,
                          const TransitionFlags* required, int requiredCount) {
    if (required == nullptr || requiredCount <= 0) return 1;
    const int32_t eventCount = entry->numConditions;
    const auto* replay = static_cast<const uint8_t*>(g_pReplayStateData);
    for (int i = 0; i < requiredCount; ++i) {
        bool found = false;
        if (eventCount > 0) {
            const auto* ring = rage::load_ptr32<CameraConditionRing>(replay, 0x68D1C);
            const auto* events = ring->entries.get();
            const int32_t capacity = ring->capacity;
            uint32_t index = static_cast<uint32_t>(entry->firstCondition);
            for (int n = 0; n < eventCount; ++n, ++index) {
                const int32_t offset = ringRemainder(static_cast<int32_t>(index), capacity);
                if (conditionEqual(events[offset], required[i])) {
                    found = true;
                    break;
                }
            }
        }
        if (!found) return 0;
    }
    return 1;
}

// Find the first eligible time, then search that suffix for a matching mode
// and condition slice. The output's second word stays unchanged.
// @ 0x82216E08 | size: 0x15C
uint8_t pongCameraMgr_6E08(void* object, TransitionParams* key,
                          int mode, void* flags, int requiredCount) {
    const auto* ring = static_cast<const CameraTransitionRing*>(object);
    const int32_t end = ring->end;
    const int32_t capacity = ring->capacity;
    int32_t cursor = ring->head;
    while (cursor != end) {
        const auto* entries = ring->entries.get();
        if (entries[cursor].key.value >= key->value) break;
        cursor = nextRingIndex(cursor, capacity);
    }
    if (cursor == end) return 0;
    const auto* entries = ring->entries.get();
    while (cursor != end) {
        const auto* entry = entries + cursor;
        if (entry->mode == mode && pongCameraMgr_5CE8(entry,
                static_cast<const TransitionFlags*>(flags), requiredCount) != 0) {
            key->value = entry->key.value;
            return 1;
        }
        cursor = nextRingIndex(cursor, capacity);
    }
    return 0;
}

// Search the half-open time interval, rewind to its first entry, then filter
// by mode and conditions. The cursor belongs to the evaluator and stays at
// the last visited entry on both success and failure.
// @ 0x82216F68 | size: 0x310
extern "C" bool pg_6F68(void* object, void* params, int mode,
                         unsigned int* flags, int requiredCount) {
    auto* ring = static_cast<CameraTransitionRing*>(object);
    auto* key = static_cast<TransitionParams*>(params);
    const auto inInterval = [key](const CameraTransitionEntry& entry) {
        float duration;
        __builtin_memcpy(&duration, &key->vtableOrState, sizeof duration);
        const float upper = key->value + duration;
        return entry.mode != 0 && entry.key.value >= key->value && entry.key.value < upper;
    };
    const auto advance = [ring]() { pg_5B10_fw(&ring->cursor, &ring->head, &ring->end); };
    const auto retreat = [ring]() { pg_5BC8_fw(&ring->cursor, &ring->head, &ring->end); };
    int32_t visited = 0;
    for (;;) {
        if (visited >= ring->count) return false;
        if (inInterval(ring->entries.get()[ring->cursor])) break;
        advance();
        visited = static_cast<int32_t>(static_cast<uint32_t>(visited) + 1u);
    }
    const int32_t firstFound = ring->cursor;
    do {
        retreat();
    } while (inInterval(ring->entries.get()[ring->cursor]) && ring->cursor != firstFound);
    advance();
    auto* entry = ring->entries.get() + ring->cursor;
    const auto matches = [mode, flags, requiredCount](const CameraTransitionEntry* candidate) {
        return candidate->mode == mode && pongCameraMgr_5CE8(candidate,
            reinterpret_cast<const TransitionFlags*>(flags), requiredCount) != 0;
    };
    if (matches(entry)) {
        key->value = entry->key.value;
        return true;
    }
    advance();
    const int32_t scanStart = ring->cursor;
    for (;;) {
        entry = ring->entries.get() + ring->cursor;
        if (!inInterval(*entry)) return false;
        if (matches(entry)) {
            key->value = entry->key.value;
            return true;
        }
        advance();
        if (ring->cursor == scanStart) return false;
    }
}

// @ 0x821F3B28 | size: 0x5C
bool pg_3B28_fw(TransitionParams* key, void* evaluator) {
    TransitionFlags flags = {3, 1};
    return pg_6F68(evaluator, key, 5, &flags.flag1, 1);
}

extern "C" uint32_t g_cameraLerpState; // @ 0x826064C4
extern "C" float g_cameraShotChangeGate; // @ 0x825C5EBC
extern "C" const float g_cameraTransitionOffset; // @ 0x8202D168

// The original's two unused argument positions precede the requested count.
// Compare the snapshotted count after querying both ends of the shot interval.
// @ 0x821F7CD8 | size: 0x120
bool pg_7CD8_2h(pongCameraMgr* source, void* evaluator, int, int, int count) {
    const uint32_t snapshot = g_cameraLerpState;
    const float gate = g_cameraShotChangeGate;
    // Unordered gate comparisons reject; unordered distances use the far case.
    if (!(gate > 0.0f)) return gate <= 0.0f && snapshot == static_cast<uint32_t>(count);
    TransitionParams key;
    __builtin_memcpy(&key, source, sizeof key);
    float duration;
    __builtin_memcpy(&duration, &key.vtableOrState, sizeof duration);
    key.value += duration;
    if (!pg_6F68(evaluator, source, 5, nullptr, -1)) return false;
    const float current = *reinterpret_cast<const float*>(source);
    if (!pongCameraMgr_3500_fw(reinterpret_cast<pongCameraMgr*>(&key), evaluator, 5)) return false;
    const float difference = current - key.value;
    const float distance = __builtin_fabsf(difference);
    const uint32_t requested = static_cast<uint32_t>(count);
    return snapshot == (!(distance < g_cameraTransitionOffset) ? requested - 2u : requested - 1u);
}

// Both the forward event and interval query must stay within the original
// clamp bound. Commit the local result only after both calls succeed.
// @ 0x821F7338 | size: 0xE4
extern "C" bool pongCameraMgr_7338_helper(void* source, void* evaluator) {
    const float current = *static_cast<const float*>(source);
    const float threshold = g_cameraThreshold;
    const float lower = threshold - current >= 0.0f ? current : threshold;
    const float upper = current - threshold >= 0.0f ? current : threshold;
    TransitionParams key;
    __builtin_memcpy(&key, source, sizeof key);
    key.value = lower;
    TransitionFlags flags = {3, 1};
    if (pongCameraMgr_6E08(evaluator, &key, 7, &flags, 1) == 0 || key.value > upper)
        return false;
    if (!pg_6F68(evaluator, &key, 16, &flags.flag1, 1) || key.value > upper)
        return false;
    *static_cast<float*>(source) = key.value;
    return true;
}

// @ 0x821F7818 | size: 0xBC
void pg_7818(CamShotKey* source) {
    TransitionParams key;
    __builtin_memcpy(&key, source, sizeof key);
    void* evaluator = rage::load_ptr32<void>(g_pReplayStateData, 0x68D18);
    TransitionFlags flags = {3, 0};
    if (pg_6F68(evaluator, &key, 5, &flags.flag1, 1) || pg_3B28_fw(&key, evaluator))
        ++g_cameraLerpState;
}

// @ 0x821F3500 | size: 0x9C
bool pongCameraMgr_3500_fw(pongCameraMgr* self, void* evaluator, int mode) {
    const float current = *reinterpret_cast<const float*>(self);
    const float threshold = g_cameraThreshold;
    const float lower = threshold - current >= 0.0f ? current : threshold;
    const float upper = current - threshold >= 0.0f ? current : threshold;
    TransitionParams key;
    __builtin_memcpy(&key, self, sizeof key);
    key.value = lower;
    if (pongCameraMgr_6E08(evaluator, &key, mode, nullptr, -1) == 0 || key.value > upper)
        return false;
    *reinterpret_cast<float*>(self) = key.value;
    return true;
}

// @ 0x821F35A0 | size: 0xAC
bool pongCameraMgr_35A0_fw(pongCameraMgr* self, void* gameState, int mode) {
    const float current = *reinterpret_cast<const float*>(self);
    const float threshold = g_cameraThreshold;
    const float lower = threshold - current >= 0.0f ? current : threshold;
    const float upper = current - threshold >= 0.0f ? current : threshold;
    TransitionParams params;
    __builtin_memcpy(&params, self, sizeof params);
    params.value = lower;
    TransitionFlags flags = {3u, 0u};
    if (pongCameraMgr_6E08(gameState, &params, mode, &flags, 1) == 0 || params.value > upper)
        return false;
    *reinterpret_cast<float*>(self) = params.value;
    return true;
}

// @ 0x821F3650 | size: 0xAC
bool pongCameraMgr_3650_fw(pongCameraMgr* self, void* gameState, int mode) {
    const float current = *reinterpret_cast<const float*>(self);
    const float threshold = g_cameraThreshold;
    const float lower = threshold - current >= 0.0f ? current : threshold;
    const float upper = current - threshold >= 0.0f ? current : threshold;
    TransitionParams params;
    __builtin_memcpy(&params, self, sizeof params);
    params.value = lower;
    TransitionFlags flags = {3u, 1u};
    if (pongCameraMgr_6E08(gameState, &params, mode, &flags, 1) == 0 || params.value > upper)
        return false;
    *reinterpret_cast<float*>(self) = params.value;
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCameraMgr_B9B0_g @ 0x8220B9B0 | size: 0x170
//
// Camera-slot ring-buffer grow helper. Reads current size (half-word at
// self+4) and capacity (half-word at self+6). When size == capacity it:
//   1. computes a new capacity = (capacity + 16) * 24
//   2. calls rage_Alloc to acquire a new buffer
//   3. zeros the new region
//   4. copies existing entries (size entries, 24 bytes each) into the new buffer
//   5. frees the old buffer (via atSingleton::Find_90D0 vtable slot 2)
//   6. stores the new buffer pointer at self+0 and returns nullptr.
// The function always bumps the size count (half-word at self+4) by one and
// returns the address of the new slot.
//
// Return: pointer to the newly-allocated slot inside the buffer
//         (base + size*24). Callers then populate that slot.
// ─────────────────────────────────────────────────────────────────────────────
void* pongCameraMgr_B9B0_g(void* self, int /*arg*/) {
    if (!self) return nullptr;

    uint8_t* mgr = static_cast<uint8_t*>(self);
    uint16_t* pCapacity = reinterpret_cast<uint16_t*>(mgr + 6);
    uint16_t* pSize     = reinterpret_cast<uint16_t*>(mgr + 4);
    void**    pBuf      = reinterpret_cast<void**>(mgr + 0);

    uint16_t capacity = *pCapacity;
    uint16_t size     = *pSize;

    if (size == capacity) {
        // Grow by 16 entries; clamp to 0xAAAA to avoid the mul-by-24 overflow
        // that the PPC code traps on (`twlgei r4,-1`).
        uint32_t newCapacity = static_cast<uint32_t>(capacity) + 16u;
        if (newCapacity > 0xAAAAu) newCapacity = 0xAAAAu;

        *pCapacity = static_cast<uint16_t>(newCapacity);
        uint32_t bytes = newCapacity * 24u;  // rlwinm *3,0,28

        // Allocate a fresh buffer through the current thread allocator.
        extern void* rage_Alloc(uint32_t);
        void* newBuf = rage_Alloc(bytes);
        if (newBuf) {
            std::memset(newBuf, 0, bytes);

            // Copy existing entries (6 x u32 = 24 bytes per slot).
            if (*pBuf != nullptr && size != 0) {
                uint8_t* oldBuf = static_cast<uint8_t*>(*pBuf);
                uint8_t* dst    = static_cast<uint8_t*>(newBuf);
                for (uint32_t i = 0; i < size; ++i) {
                    std::memcpy(dst + i * 24u, oldBuf + i * 24u, 24u);
                }

                // Release the old buffer. Engine path goes through a
                // singleton-checked dtor vtable slot — left deferred until
                // the proto-RAGE free-path is lifted. Leaking here matches
                // the previous stubbed behaviour (this helper is cold).
            }
            *pBuf = newBuf;
        }
    }

    // Bump the size counter and return the address of the newly-acquired slot.
    uint16_t slot = *pSize;
    *pSize = static_cast<uint16_t>(slot + 1);
    if (*pBuf == nullptr) return nullptr;
    return static_cast<uint8_t*>(*pBuf) + slot * 24u;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCameraMgr_ValidateTransition — synthetic glue symbol used by
// pong_camera.cpp::TryTransition. The real validator at 0x821F3500 _is_
// pongCameraMgr_3500_fw above, but the TryTransition path wraps it with
// a full flags block. We delegate to 6E08 directly here, preserving the
// contract the caller already assumes.
// ─────────────────────────────────────────────────────────────────────────────
uint8_t pongCameraMgr_ValidateTransition(void* gameState,
                                                     TransitionParams* params,
                                                     int mode,
                                                     TransitionFlags* flags,
                                                     int enable) {
    return pongCameraMgr_6E08(gameState, params, mode, flags, enable);
}

// ─────────────────────────────────────────────────────────────────────────────
// C-linkage helpers used by the pong_camera.cpp wrapper methods.
// Keep these in an extern "C" block so the declarations at pong_camera.cpp
// lines 522-697 resolve without mangling mismatches.
// ─────────────────────────────────────────────────────────────────────────────
extern "C" {

/**
 * pongCameraMgr_FloatThresholdA — returns true iff *self > threshold.
 * Used by CheckThreshold7550.
 */
bool pongCameraMgr_FloatThresholdA(void* self, float threshold) {
    if (!self) return false;
    float current = *static_cast<const float*>(self);
    return (current - threshold) > 0.0f;
}

/**
 * pongCameraMgr_FloatThresholdB — returns true iff *self > 0.
 * Used by the 7588/75C8/7608/7648/7688 quintuplet.
 */
bool pongCameraMgr_FloatThresholdB(void* self) {
    if (!self) return false;
    float current = *static_cast<const float*>(self);
    return current > 0.0f;
}

/**
 * pongCameraMgr_QueryA / B / C — paired camera-slot predicates.
 *
 * The recomp resolves these to the same three addresses as the
 * clamp-dispatch wrappers above (A=3500, B=35A0, C=3650). The callers in
 * pong_camera.cpp feed a local `stateCopy` uint64_t (first 8 bytes of the
 * camera mgr) as `self`, not a real camera object. Route directly into the
 * corresponding `_fw` worker.
 */
bool pongCameraMgr_QueryA(void* stateCopy, int index) {
    return pongCameraMgr_3500_fw(static_cast<pongCameraMgr*>(stateCopy),
                                 nullptr, index);
}

bool pongCameraMgr_QueryB(void* stateCopy, int index) {
    return pongCameraMgr_35A0_fw(static_cast<pongCameraMgr*>(stateCopy),
                                 nullptr, index);
}

bool pongCameraMgr_QueryC(void* stateCopy, int index) {
    return pongCameraMgr_3650_fw(static_cast<pongCameraMgr*>(stateCopy),
                                 nullptr, index);
}

}  // extern "C"
