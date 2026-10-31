#pragma once
#include <stdint.h>

/* Kernel import snapshot. Only +0x10 is recovered; the preceding words are
 * deliberately opaque. Host snapshots live outside the game's pointer arena. */
typedef struct {
    uint8_t reserved[0x10];
    uint32_t milliseconds;
} KeTimeStampBundle;

#ifdef __cplusplus
extern "C" {
#endif
uint32_t tt_uptime_milliseconds(void);
const KeTimeStampBundle* hostGetKeTimeStampBundle(void);
#ifdef __cplusplus
}
#endif
