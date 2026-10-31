#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
// One image word holds the render object normally, or a small integer sentinel
// on the GPU watchdog's fatal path. uintptr_t retains native pointer width.
extern uintptr_t g_grcProgressState; // @ 0x82606654
#ifdef __cplusplus
}

inline void* grcProgressRenderObject() {
    return reinterpret_cast<void*>(g_grcProgressState);
}
#endif
