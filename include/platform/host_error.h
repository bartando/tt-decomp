#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// Native Win32-style last-error state; each host thread owns its own value.
void hostSetLastError(uint32_t error);
uint32_t hostGetLastError(void);
#ifdef __cplusplus
}
#endif
