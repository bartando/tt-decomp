#pragma once
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif
// MSVC _snprintf: fill up to count bytes; terminate only when text is shorter.
int _snprintf(char* buffer, size_t count, const char* format, ...); // @ 0x820C0B40
#ifdef __cplusplus
}
#endif
