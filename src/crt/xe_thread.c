#include <stdint.h>

/* Host representation of the Xbox r13 register. */
extern void* g_sda_base; /* @ 0x82600000 */

/* xe_GetCurrentThreadId @ 0x82566B78 */
uint32_t xe_GetCurrentThreadId(void) {
    const uint8_t* thread = *(const uint8_t**)((const uint8_t*)g_sda_base + 0x100);
    return *(const uint32_t*)(thread + 0x14C);
}

/* Legacy callers use the old name and treat the returned ID as a pointer. */
void* _crt_tls_fiber_setup(void) {
    return (void*)(uintptr_t)xe_GetCurrentThreadId();
}
