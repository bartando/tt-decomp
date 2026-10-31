#include <cstdint>
#include <cstdlib>
#include <pthread.h>
#include "link/tt_alias.h"

// @ 0x825F3860 — words occupied in the selected queue bank.
extern "C" uint32_t g_gameMessageQueueWords = 0;
// @ 0x825EE297 — selects one of two 1024-word banks.
extern "C" uint8_t g_gameMessageQueueBank = 0;
// @ 0x825F3AA8
extern "C" alignas(16) uint8_t g_gameMessageQueue[8192] = {};

// RtlEnterCriticalSection's POSIX backend operates on a pthread mutex. Use
// native-sized storage and recursion, including nested immediate messages.
extern "C" pthread_mutex_t g_nativeGameMessageQueueMutex;
pthread_mutex_t g_nativeGameMessageQueueMutex;
TT_DATA_ALIAS("g_gameMessageQueueLock", "g_nativeGameMessageQueueMutex"); // @ 0x82619DA0

namespace {
struct InitializeQueueMutex {
    InitializeQueueMutex() {
        pthread_mutexattr_t attributes;
        if (pthread_mutexattr_init(&attributes) != 0) std::abort();
        if (pthread_mutexattr_settype(&attributes, PTHREAD_MUTEX_RECURSIVE) != 0) std::abort();
        if (pthread_mutex_init(&g_nativeGameMessageQueueMutex, &attributes) != 0) std::abort();
        pthread_mutexattr_destroy(&attributes);
    }
} initializeQueueMutex;
}
