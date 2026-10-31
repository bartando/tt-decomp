#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
void grcDevice_SetScissorRect(void* device, int32_t left, int32_t top,
                              int32_t right, int32_t bottom); // @ 0x823537B0
void grcDevice_FlushRenderState(void); // @ 0x8215B138
void grc_36E8(void* device, void* surface); // @ 0x823536E8
void grc_5E08(void* device, const void* rect); // @ 0x82355E08
void rage_6858(void* device, uint32_t index, const float* plane); // @ 0x82356858
uint32_t* grc_DBF8(void* device, uint32_t* cursor); // @ 0x8235DBF8
void grc_3410(void* device); // @ 0x82363410
void grc_3E20(void* device); // @ 0x82363E20
#ifdef __cplusplus
}
#endif
