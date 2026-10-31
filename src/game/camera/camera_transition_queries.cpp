#include "game/camera_queries.hpp"

struct pongCameraMgr;
bool pongCameraMgr_3500_fw(pongCameraMgr* key, void* evaluator, int mode); // @ 0x821F3500
uint8_t pongCameraMgr_6E08(void* evaluator, TransitionParams* key,
                          int mode, void* flags, int enable); // @ 0x82216E08
extern "C" const float g_cameraConstPool[32]; // @ 0x8202D108
extern "C" float g_cameraThreshold; // @ 0x825C5EC0

// Query mode 20 first. Its edits to the local key's second word survive into
// the mode-3 query, whose first word comes from the live source plus one.
// @ 0x821F6990 | size: 0x8C
bool pongCameraMgr_6990(void* source, void* evaluator) {
    TransitionParams copy;
    __builtin_memcpy(&copy, source, sizeof copy);
    if (!pongCameraMgr_3500_fw(reinterpret_cast<pongCameraMgr*>(&copy), evaluator, 20))
        return false;
    copy.value = *static_cast<float*>(source) + g_cameraConstPool[0];
    return pongCameraMgr_3500_fw(reinterpret_cast<pongCameraMgr*>(&copy), evaluator, 3);
}

// Clamp the query key to the threshold; accept a returned NaN just as the
// original's ordered bgt test does. Only the source float is written back.
// @ 0x821F5308 | size: 0xB0
bool pongCameraMgr_5308_fw(void* source, void* evaluator) {
    const float current = *static_cast<float*>(source);
    const float threshold = g_cameraThreshold;
    const float lower = threshold - current >= 0.0f ? current : threshold;
    const float upper = current - threshold >= 0.0f ? current : threshold;
    TransitionParams copy;
    __builtin_memcpy(&copy, source, sizeof copy);
    copy.value = lower;
    TransitionFlags flags = {5, 0};
    if (pongCameraMgr_6E08(evaluator, &copy, 6, &flags, 1) == 0 || copy.value > upper)
        return false;
    *static_cast<float*>(source) = copy.value;
    return true;
}
