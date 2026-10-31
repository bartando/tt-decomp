#include "rage/swf_state.hpp"
#include "rage/hud_page_group.hpp"
#include <cstdint>

extern void* g_swfStringPool;      // @ 0x82604C50
extern void* g_swfScriptObjectPool;// @ 0x82604C60
extern void* g_swfScriptArrayPool; // @ 0x82604C58
extern void* g_swfTextPool;        // @ 0x82602844
namespace rage {
extern void* g_swfGlobalObject;    // @ 0x82602818
extern void* g_swfGlobalScope;     // @ 0x8260282C
extern void* g_swfAuxiliaryScope;  // @ 0x82602834
}

namespace {
struct SwfPageGroupView {
    uint8_t _pad00[0x24];
    uint8_t stringPool[0x14];  // +0x24
    uint8_t nodePool[0x14];    // +0x38
    uint8_t memberPool[0x14];  // +0x4C
    uint8_t objectPool[0x14];  // +0x60
    uint8_t arrayPool[0x14];   // +0x74
    uint8_t textPool[0x14];    // +0x88
    void* globalObject;       // +0x9C
    void* globalScope;        // +0xA0
    void* auxiliaryScope;     // +0xA4
    uint8_t active;           // +0xA8
};
struct SwfScopeView {
    void* dispatch;           // +0x00
    uint32_t members[2];      // +0x04
};
}

uint32_t* swfFindMember(void* list, const char* key); // @ 0x823FB3B8
void swfSetMember(void* list, const char* key, const uint32_t* value); // @ 0x823FB258

// @ 0x823F9040 | size: 0x88
void swfSelectPageGroup(void* object, uint32_t bindGlobals) {
    auto* group = static_cast<SwfPageGroupView*>(object);
    if (group->active != 0) return;
    g_swfStringPool = group->stringPool;
    g_swfNodePool = group->nodePool;
    g_swfMemberNodePool = group->memberPool;
    g_swfScriptObjectPool = group->objectPool;
    g_swfScriptArrayPool = group->arrayPool;
    g_swfTextPool = group->textPool;
    if ((bindGlobals & 0xFFu) != 0) {
        rage::g_swfGlobalObject = group->globalObject;
        rage::g_swfGlobalScope = group->globalScope;
        rage::g_swfAuxiliaryScope = group->auxiliaryScope;
    }
}

// @ 0x823F9318 | size: 0xB4
extern "C" void* SinglesNetworkClient_BindEntry(void* object, const char* key) {
    auto* group = static_cast<SwfPageGroupView*>(object);
    swfSelectPageGroup(group, 1);
    // Keep the scope selected at entry even if a dictionary callback changes
    // the globals. The original retains it in r29 for the retry as well.
    auto* scope = static_cast<SwfScopeView*>(rage::g_swfGlobalScope);
    uint32_t* entry = swfFindMember(scope->members, key);
    if (!entry) {
        const uint32_t zeroNumber[2] = {0, 3};
        swfSetMember(scope->members, key, zeroNumber);
        entry = swfFindMember(scope->members, key);
    }
    // Reload active after the callbacks. Array-pool binding intentionally
    // survives this cleanup: retail does not clear 0x82604C58 here.
    if (group->active == 0) {
        rage::g_swfGlobalScope = nullptr;
        g_swfStringPool = nullptr;
        g_swfNodePool = nullptr;
        g_swfMemberNodePool = nullptr;
        g_swfScriptObjectPool = nullptr;
        g_swfTextPool = nullptr;
        rage::g_swfGlobalObject = nullptr;
        rage::g_swfAuxiliaryScope = nullptr;
    }
    return entry;
}
