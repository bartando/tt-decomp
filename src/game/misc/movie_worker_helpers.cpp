#include "game/movie_worker_helpers.hpp"
#include "pong_misc.hpp"

extern "C" uint32_t xe_GetCurrentThreadId(); // @ 0x82566B78

namespace {
// These helpers operate on a ring buffer, not on the movie player's unrelated
// fields at the same offsets. Keep arithmetic unsigned, including wraparound.
struct RingIndices {
    uint8_t unused[0x34];
    uint32_t capacity;
    uint32_t writeIndex;
    uint32_t readIndex;
    uint8_t unused40[4];
    uint32_t freeSlots;
};
static_assert(offsetof(RingIndices, freeSlots) == 0x44, "ring counter offset");
}

// @ 0x8248DCC8 | size: 0x68
void CCalRingBuffer_CommitWrite(void* object) {
    auto* ring = static_cast<RingIndices*>(object);
    const uint32_t next = ring->writeIndex + 1u;
    ring->writeIndex = next >= ring->capacity ? 0u : next;
    __atomic_fetch_sub(&ring->freeSlots, 1u, __ATOMIC_RELAXED);
}

// @ 0x8248DD30 | size: 0x68
void CCalRingBuffer_ReleaseRead(void* object) {
    auto* ring = static_cast<RingIndices*>(object);
    const uint32_t next = ring->readIndex + 1u;
    ring->readIndex = next >= ring->capacity ? 0u : next;
    __atomic_fetch_add(&ring->freeSlots, 1u, __ATOMIC_RELAXED);
}

// @ 0x8235EB30 | size: 0x40
uint32_t CCalMoviePlayer_AcquireFiberContext(void* object) {
    auto* threadId = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(object) + 0x2888);
    if (*threadId != 0) xe_GetCurrentThreadId();
    return *threadId = xe_GetCurrentThreadId();
}

// Worker entry points discard the virtual's result and return success.
// @ 0x8248EC88 | size: 0x30
int32_t CCalMoviePlayer_EC88_p33(void* object) {
    static_cast<CCalMoviePlayer*>(object)->MediaControl_Pause();
    return 0;
}
// @ 0x8248ECB8 | size: 0x30
int32_t CCalMoviePlayer_ECB8_p33(void* object) {
    static_cast<CCalMoviePlayer*>(object)->MediaControl_Stop();
    return 0;
}
// @ 0x8248ECE8 | size: 0x30
int32_t CCalMoviePlayer_ECE8_p33(void* object) {
    static_cast<CCalMoviePlayer*>(object)->MediaControl_GetState();
    return 0;
}
// @ 0x8248ED18 | size: 0x30
int32_t CCalMoviePlayer_ED18_p33(void* object) {
    static_cast<CCalMoviePlayer*>(object)->MediaControl_StopWhenReady();
    return 0;
}
