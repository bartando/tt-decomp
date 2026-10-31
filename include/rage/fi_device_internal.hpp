#pragma once
#include "rage/fi_stream.hpp"
namespace rage {
struct fiDeviceMount {
    char prefix[0x104];
    uint16_t reserved104;
    uint16_t readOnly;
    uint16_t prefixLength;
    uint16_t reserved10A;
    ptr32<ptr32<fiStreamDevice>> devices;
    uint16_t count;
    uint16_t capacity;
};
static_assert(sizeof(fiDeviceMount) == 0x114);
static_assert(offsetof(fiDeviceMount, devices) == 0x10C);
struct fiDeviceMountTable {
    ptr32<fiDeviceMount> entries;
    uint16_t count;
    uint16_t capacity;
};
}
extern "C" {
extern rage::fiDeviceMountTable lbl_8262F368; // @ 0x8262F368
extern uint8_t lbl_825D0074[]; // @ 0x825D0074 — memory device object
extern uint8_t lbl_825D06C4[]; // @ 0x825D06C4 — TCP/IP device object
extern uint8_t lbl_825D0070[]; // @ 0x825D0070 — local device object
extern rage::ptr32<rage::fiStreamDevice> lbl_825C481C; // @ 0x825C481C
extern uint8_t g_fiFallbackReadOnly; // @ 0x826065EA
int32_t fiDevice_ComparePrefix(const char* left, const char* right, uint32_t bytes); // @ 0x822E1218
}
