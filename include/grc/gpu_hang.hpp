#pragma once
#include "rage/ptr32.hpp"
#include <cstdint>

struct grcGpuHangState {
    rage::ptr32<void> device;
    uint32_t lastGpuTick;
    uint32_t lastQueueHead;
};
static_assert(sizeof(grcGpuHangState) == 12);
int D3DDeviceXenon_ReportGPUHang(void* state); // @ 0x823643E0
