/**
 * heap.c — CRT Heap Management Stubs
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Allocation stubs and the RAGE allocator-dispatching free wrapper.
 */

#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "rage/rage_allocator.h"
#include "rage/singleton.h"

extern void* g_sda_base; /* @ 0x82600000 */

/**
 * rage_AllocInternal — RAGE engine allocation function @ 0x820C01B8
 * Allocates memory with the given size and flags.
 * Flags are Xbox 360 specific allocation attributes (alignment, caching).
 */
void* rage_AllocInternal(uint32_t size, uint32_t flags) {
    (void)flags;  /* Flags are Xbox 360 specific — ignored on host */
    return malloc(size);
}

/**
 * rage_free — RAGE engine free function @ 0x820C00C0
 * Skips null and singleton-owned pointers, then dispatches to the thread allocator.
 */
void rage_free(void* ptr) {
    if (!ptr || (uint8_t)rage_FindSingleton(ptr))
        return;
    void** tls = *(void***)g_sda_base;
    rageAllocator* allocator = (rageAllocator*)tls[1];
    allocator->vtable->Free(allocator, ptr);
}

/* rage_free_00C0 was an alias — merged with rage_free above */

/**
 * rage_alloc — Allocate zeroed memory @ 0x820CEC88
 */
void* rage_alloc(uint32_t size) {
    void* ptr = malloc(size);
    if (ptr) {
        memset(ptr, 0, size);
    }
    return ptr;
}
