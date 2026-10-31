#pragma once
#include <cstdint>
#include "rage/swf_page_group.hpp"

// Retail Flash page-group accessors. The historical "network dirty" names
// refer to the shared Flash semaphore, not to network synchronization.
extern "C" uint32_t hudFlashBase_IsNetworkDirty(void* hud); // @ 0x822EB2A8
extern "C" void* hudFlashBase_GetPageGroup(void* hud);      // @ 0x822EB1E8
extern "C" void hudFlashBase_PublishPageGroup(void* hud);   // @ 0x822EB320
