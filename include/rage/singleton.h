#pragma once

/**
 * singleton.h — RAGE atSingleton Registry
 * Rockstar Presents Table Tennis (Xbox 360)
 *
 * The atSingleton registry tracks singleton-owned memory regions.
 * The heap free path (rage_free, sysMemAllocator_Free) checks this
 * registry to avoid freeing memory that belongs to a singleton subsystem.
 */

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * rage_FindSingleton @ 0x820F90D0 | size: 0xA4
 *
 * Checks if a pointer is owned by a registered singleton.
 * Returns 1 if the pointer belongs to a singleton (do NOT free).
 * Returns zero if the pointer is not singleton-owned (safe to free).
 *
 * The 32-bit result models guest r3; callers that test its low byte keep
 * that explicit, as in the original PowerPC code.
 */
uint32_t rage_FindSingleton(void* ptr);

#ifdef __cplusplus
}  /* extern "C" */
#endif
