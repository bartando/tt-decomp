/**
 * kernel_import_thunks.c — the image's xboxkrnl import thunks
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * The game calls kernel exports through thunks at the end of .text (the
 * loader patches each to jump to the export). Code that calls a thunk by its
 * address-suffixed name gets it here, forwarding to the port's kernel.c.
 */

#include <stdint.h>

uint32_t KeTlsAlloc(void);
void* KeTlsGetValue(uint32_t index);

/* @ 0x8258623C — thunk for xboxkrnl ordinal 0x152, KeTlsAlloc */
uint32_t ke_KeTlsAlloc_623C(void) {
    return KeTlsAlloc();
}

/* @ 0x8258621C — thunk for xboxkrnl ordinal 0x154, KeTlsGetValue */
void* ke_KeTlsGetValue_621C(uint32_t index) {
    return KeTlsGetValue(index);
}
