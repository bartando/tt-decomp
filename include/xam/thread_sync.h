#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

int64_t* sysThread_MillisecondsTimeout(int64_t* storage, uint32_t milliseconds); // @ 0x8242C390
uint32_t sysThread_SetErrorFromStatus(int32_t status); // @ 0x8242C330
uint32_t sysThread_SetErrorFromStatusThunk(int32_t status); // @ 0x8242BF10
uint32_t sysThread_WaitTimeoutEx(void* handle, uint32_t milliseconds, uint32_t alertable); // @ 0x8242F5D0
uint32_t sysThread_WaitTimeout(void* handle, int milliseconds) __asm__("_pg_C3B8_g"); // @ 0x8242C3B8
uint32_t sysThread_ReleaseSemaphore(void* handle, int32_t count,
                                  int32_t* previousCount) __asm__("_pg_6DC0_g"); // @ 0x82566DC0

#ifdef __cplusplus
}
#endif
