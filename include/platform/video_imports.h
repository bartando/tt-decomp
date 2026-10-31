#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// Native import slots hold host pointer widths. A null device means the Xenon
// video backend is unavailable; it is never a fabricated guest device address.
extern void** __imp_VdGlobalDevice;     // @ 0x82000730
extern void** __imp_VdGlobalXamDevice;  // @ 0x82000734
uint32_t KeGetCurrentProcessType(void); // @ 0x82585E9C
#ifdef __cplusplus
}
#endif
