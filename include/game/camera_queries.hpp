#pragma once
#include <cstdint>

// Camera query keys are copied with a single eight-byte load/store.
struct TransitionParams {
    float value;
    uint32_t vtableOrState;
};
struct TransitionFlags {
    uint32_t flag1;
    uint32_t flag2;
};
static_assert(sizeof(TransitionParams) == 8, "camera query key size");

extern "C" {
bool pongCameraMgr_6990(void* key, void* evaluator); // @ 0x821F6990
bool pongCameraMgr_5308_fw(void* key, void* evaluator); // @ 0x821F5308
}

float gameLoop_GetDisplayAspect(void* gameLoop); // @ 0x82228EA0
