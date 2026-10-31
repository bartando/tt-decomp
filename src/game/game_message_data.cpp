#include <cstdint>
#include <cstdlib>
#include "xam/kernel.h"
#include "link/tt_alias.h"

// @ 0x825F3860 — words occupied in the selected queue bank.
extern "C" uint32_t g_gameMessageQueueWords = 0;
// @ 0x825EE297 — selects one of two 1024-word banks.
extern "C" uint8_t g_gameMessageQueueBank = 0;
// @ 0x825F3AA8
extern "C" alignas(16) uint8_t g_gameMessageQueue[8192] = {};

// Native backends share the guest critical-section representation. Its opaque
// lock is initialized lazily, including recursive immediate-message delivery.
extern "C" RTL_CRITICAL_SECTION g_nativeGameMessageQueueMutex;
RTL_CRITICAL_SECTION g_nativeGameMessageQueueMutex = {};
TT_DATA_ALIAS("g_gameMessageQueueLock", "g_nativeGameMessageQueueMutex"); // @ 0x82619DA0
