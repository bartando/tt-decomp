#include "rage/hud_page_group.hpp"
#include <cstdint>

namespace {
struct FlashManager {
    uint8_t _pad00[0x34];
    void* semaphore; // +0x34
};
struct FlashGameLoop {
    uint8_t _pad000[0x22C];
    FlashManager* manager; // +0x22C
};
struct FlashHud {
    uint8_t _pad00[0x5C];
    void* pageGroup; // +0x5C
};
}

extern void* g_loop_obj_ptr;        // @ 0x825EAB30
extern uint8_t g_bNetworkDebugFlag; // @ 0x826065EB — shared Flash semaphore held
extern "C" uint32_t sysThread_WaitTimeout(void* handle, int timeout) __asm__("_pg_C3B8_g"); // @ 0x8242C3B8
extern "C" uint32_t sysThread_ReleaseSemaphore(void* handle, int32_t count,
                                               int32_t* previousCount); // @ 0x82566DC0
extern "C" void rage_debugLog(const char* text); // @ 0x8240E6D0

// @ 0x822EB2A8 | size: 0x78
extern "C" uint32_t hudFlashBase_IsNetworkDirty(void* /*unused*/) {
    auto* loop = static_cast<FlashGameLoop*>(g_loop_obj_ptr);
    FlashManager* manager = loop->manager;
    if (!manager || g_bNetworkDebugFlag != 0) return 0;
    sysThread_WaitTimeout(manager->semaphore, -1);
    g_bNetworkDebugFlag = 1;
    return 1;
}

// @ 0x822EB1E8 | size: 0x5C
extern "C" void* hudFlashBase_GetPageGroup(void* hud) {
    auto* loop = static_cast<FlashGameLoop*>(g_loop_obj_ptr);
    if (loop->manager && g_bNetworkDebugFlag == 0) {
        rage_debugLog("[*** FLASHBASE ERROR ***] Updating without grabbing flash sema!");
    }
    // Reload after the diagnostic callback, as the PPC does.
    return static_cast<FlashHud*>(hud)->pageGroup;
}

// @ 0x822EB320 | size: 0x60
extern "C" void hudFlashBase_PublishPageGroup(void* /*unused*/) {
    auto* loop = static_cast<FlashGameLoop*>(g_loop_obj_ptr);
    FlashManager* manager = loop->manager;
    if (manager && g_bNetworkDebugFlag != 0) {
        sysThread_ReleaseSemaphore(manager->semaphore, 1, nullptr);
        g_bNetworkDebugFlag = 0;
    }
}
