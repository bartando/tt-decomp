// Clip lifecycle for the inline crAnimBlenderState.
#include <cstdint>
#include <cstddef>
#include "rage/sys_callback.hpp"

extern "C" uint32_t g_sceneResetMatrix[4]; // @ 0x8261A0C0
extern "C" void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0

void sysCallback_Destroy(void*); // @ 0x821E7BC0
void crAnimBlenderState_Init(void*); // @ 0x8224C810
void crAnimBlenderState_Stop(void*); // @ 0x8224CEA8

namespace {
using Cleanup = void (*)(void*);
struct CleanupCallback {
    Cleanup cleanup;
    uintptr_t unused;
    void* target;
    Cleanup release;
};

struct BlenderState {
    void* vtable;                       // +00
    uint8_t pad04[12];
    uintptr_t notification[4];         // +10
    CleanupCallback onStop;            // +20
    CleanupCallback onComplete;        // +30
    uint32_t counter;                  // +40
    const void* clip;                  // +44
    uint16_t status;                   // +48
    uint16_t flags;                    // +4A
    uint8_t pad4C[4];
    float phase;                      // +50
    float previousPhase;              // +54
    uint8_t pad58[32];
    float rate;                       // +78
    float phaseOffset;                // +7C
    float weight;                     // +80
    float weightOffset;               // +84
    float targetWeight;               // +88
    uint16_t channelFlags;             // +8C
    uint16_t slots[3];                 // +8E
    uint8_t pad94[4];
    float blendIn;                    // +98
    float blendOut;                   // +9C
};

#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(offsetof(BlenderState, status) == 0x48, "blender state offset");
static_assert(offsetof(BlenderState, slots) == 0x8E, "blender slot offset");
static_assert(sizeof(BlenderState) == 0xA0, "blender size");
#endif

CleanupCallback emptyCallback() {
    // PPC leaves this unused word uninitialized; use a deterministic zero.
    return {reinterpret_cast<Cleanup>(nop_8240E6D0), 0,
            nullptr, sysCallback_Destroy};
}

void clearNotification(BlenderState* state) {
    for (unsigned i = 0; i < 4; ++i) state->notification[i] = g_sceneResetMatrix[i];
}
}

// The first word is the cleanup function itself, not an object's vtable.
// @ 0x821E7BC0 | size: 0xC
void sysCallback_Destroy(void* callback) {
    static_cast<CleanupCallback*>(callback)->cleanup(callback);
}

// Leave the unused gaps untouched, including the blend-data pointer at +04.
// @ 0x8224C810 | size: 0x120
void crAnimBlenderState_Init(void* object) {
    auto* state = static_cast<BlenderState*>(object);
    state->slots[1] = 0xFFFF;
    state->slots[2] = 0xFFFF;
    state->slots[0] = 0xFFFF;
    state->phase = 0.0f;
    state->previousPhase = 0.0f;
    state->rate = 1.0f;
    state->phaseOffset = 0.0f;
    state->flags = 0;
    state->weight = 1.0f;
    state->weightOffset = 0.0f;
    state->channelFlags = 0;
    state->targetWeight = 1.0f;
    state->blendIn = 0.0f;
    state->blendOut = 0.0f;
    clearNotification(state);
    state->onStop = emptyCallback();
    state->onComplete = emptyCallback();
    state->status = 0;
    state->clip = nullptr;
    state->counter = 0;
}

// Stop callbacks observe the cleared running/notification flags. The callback
// can update the state, so subsequent cleanup and stores use the live object.
// @ 0x8224CEA8 | size: 0x138
void crAnimBlenderState_Stop(void* object) {
    auto* state = static_cast<BlenderState*>(object);
    if (state->status == 0) return;
    state->flags &= ~1u;
    if (state->flags & 0x800u) {
        state->flags &= ~0x800u;
        sysCallback_Invoke(state->notification, nullptr);
        clearNotification(state);
    }
    state->onStop.release(&state->onStop);
    state->counter = 0;
    state->onStop = emptyCallback();
    state->onComplete = emptyCallback();
}

// @ 0x8224CDF0 | size: 0xB4
uint32_t util_CDF0(void* object, const void* clip, uint32_t flags) {
    auto* state = static_cast<BlenderState*>(object);
    if (state->flags & 0x100u) return 0;
    if (state->status != 0) crAnimBlenderState_Stop(state);
    crAnimBlenderState_Init(state);
    state->clip = clip;
    state->status = 1;
    state->flags |= 1;
    if (static_cast<uint8_t>(flags) != 0) state->flags |= 0x20u;
    else state->flags &= ~0x20u;
    return 1;
}
