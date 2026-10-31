#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
void grcDevice_SetScissorRect(void* device, int32_t left, int32_t top,
                              int32_t right, int32_t bottom); // @ 0x823537B0
void grcDevice_FlushRenderState(void); // @ 0x8215B138
#ifdef __cplusplus
}
#endif
