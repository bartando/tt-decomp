#include "platform/time_stamp.h"

// @ 0x82566F98 | size: 0x10
// Retail reads __imp_KeTimeStampBundle->milliseconds at +0x10. Refreshing
// that kernel-owned snapshot is the host platform's responsibility.
uint32_t atSingleton_6F98_g() {
    return hostGetKeTimeStampBundle()->milliseconds;
}
