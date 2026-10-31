#pragma once

/* Force-included for the x86 Windows build: pointer fields and image offsets
 * throughout the decompilation describe the Xbox's 32-bit address space. */
#ifdef TT_WINDOWS_X86
#ifdef __cplusplus
static_assert(sizeof(void*) == 4, "The native Windows decomp requires 32-bit pointers");
#else
_Static_assert(sizeof(void*) == 4, "The native Windows decomp requires 32-bit pointers");
#endif
#endif
