#include "rage/session_state_helpers.hpp"
#include "rage/ptr32.hpp"
#include <cstdint>

extern void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0

namespace {
struct NotifierLinks {
    uint8_t prefix[0x0C];
    rage::ptr32<NotifierLinks> previous;
    rage::ptr32<NotifierLinks> next;
    rage::ptr32<uint8_t> owner;
};
struct NotifierChain {
    uint8_t prefix[0x0C];
    rage::ptr32<NotifierLinks> head;
    rage::ptr32<NotifierLinks> tail;
    uint32_t count;
};
struct SessionContextSource {
    virtual void Unknown00() = 0;
    virtual void Unknown01() = 0;
    virtual void Unknown02() = 0;
    virtual void Unknown03() = 0;
    virtual void Unknown04() = 0;
    virtual void Unknown05() = 0;
    virtual void Unknown06() = 0;
    virtual void Unknown07() = 0;
    virtual void Unknown08() = 0;
    virtual void Unknown09() = 0;
    virtual void Unknown10() = 0;
    virtual void* GetContext() = 0;
};
}

namespace rage::snSession_States {
// @ 0x823DD170 | size: 0x80
void snSession_RegisterNotifier(snLinkedList* owner, snNotifier* notifier) {
    auto* chain = reinterpret_cast<NotifierChain*>(owner);
    auto* node = reinterpret_cast<NotifierLinks*>(notifier);
    if (chain->head) {
        auto* previous = chain->tail.get();
        auto* next = previous->next.get();
        node->next = next;
        if (next) next->previous = node;
        else chain->tail = node;
        previous->next = node;
        node->previous = previous;
    } else {
        chain->head = node;
        chain->tail = node;
        node->next = nullptr;
        node->previous = nullptr;
    }
    ++chain->count;
    node->owner = reinterpret_cast<uint8_t*>(owner) + 8;
}

// @ 0x823ED4F8 | size: 0x74
void snSession_SetTimeout(hsmStateBase* state, int32_t milliseconds) {
    auto* source = reinterpret_cast<SessionContextSource*>(state);
    auto* context = static_cast<uint8_t*>(source->GetContext());
    char scratch[80];
    nop_8240E6D0(scratch, "Setting timeout:%d ms at:%d", milliseconds,
                 *reinterpret_cast<uint32_t*>(context + 0x50));
    context[0x68] |= 0x80;
    *reinterpret_cast<uint32_t*>(context + 0x4C) =
        *reinterpret_cast<uint32_t*>(context + 0x50) + static_cast<uint32_t>(milliseconds);
}
}
