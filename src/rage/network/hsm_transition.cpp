#include "rage/hsm_transition.hpp"
#include "rage/ptr32.hpp"
#include <cstdint>

void snSession_DDB8_w(void* context, void* node); // @ 0x823EDDB8
void snSession_DD10_w(void* context, void* node); // @ 0x823EDD10
void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0

namespace {
struct ConnectionLink {
    rage::ptr32<void> vtable;
    rage::ptr32<ConnectionLink> previous;
    rage::ptr32<ConnectionLink> next;
    uint8_t flags;
};
struct ConnectionList {
    rage::ptr32<ConnectionLink> head;
    rage::ptr32<ConnectionLink> tail;
    uint32_t count;
};
struct TransitionState {
    virtual void Unknown00() = 0;
    virtual void Unknown01() = 0;
    virtual const char* GetName() = 0;
    virtual void Unknown03() = 0;
    virtual void Unknown04() = 0;
    virtual void Unknown05() = 0;
    virtual void Unknown06() = 0;
    virtual int32_t GetStatus() = 0;
    virtual void* GetNotificationNode() = 0;
    virtual void Unknown09() = 0;
    virtual void Unknown10() = 0;
    virtual void Unknown11() = 0;
    virtual void Unknown12() = 0;
    virtual void Update() = 0;
    virtual void Enter() = 0;
    virtual void Exit() = 0;
};
uint8_t* parent(void* state) { return rage::load_ptr32<uint8_t>(state, 8); }
bool contains(uint8_t* state, void* candidate) {
    while (state) {
        if (state == candidate) return true;
        state = parent(state);
    }
    return false;
}
}

// @ 0x823ED418 | size: 0xDC
void* snSession_D418_w(void* from, void* to) {
    auto* result = parent(from);
    if (from == to) return result;
    if (contains(result, to)) return parent(to);
    auto* other = parent(to);
    if (contains(other, from)) return result;
    while (result) {
        if (contains(other, result)) return result;
        result = parent(result);
    }
    return nullptr;
}

// @ 0x823ED988 | size: 0x104
void snSession_AssociateConnections(void* context, void* from, void* to) {
    auto* bytes = static_cast<uint8_t*>(context);
    const int32_t limit = *reinterpret_cast<int32_t*>(bytes + 0x58);
    const uint32_t count = *reinterpret_cast<uint32_t*>(bytes + 0x54);
    if (from && !(limit > 0 && count == static_cast<uint32_t>(limit))) {
        void* stop = snSession_D418_w(from, to);
        auto active = [&]() { return rage::load_ptr32<TransitionState>(context, 8); };
        if (active() != stop) {
            do {
                const char* name = active()->GetName();
                char scratch[80];
                nop_8240E6D0(scratch, "Leaving: %s", name);
                active()->Exit();
                void* node = active()->GetNotificationNode();
                snSession_DDB8_w(context, node);
                void* current = active();
                auto* up = parent(current);
                *reinterpret_cast<rage::ptr32<void>*>(up + 0x0C) = current;
                *reinterpret_cast<rage::ptr32<void>*>(bytes + 8) = parent(active());
            } while (active() != stop);
        }
    }
    ++*reinterpret_cast<uint32_t*>(bytes + 0x54);
    bytes[0x68] &= 0x7F;
}

// @ 0x823EDA90 | size: 0x1AC
void snSession_ProcessPendingConnections(void* context, void* unused, void* target) {
    (void)unused;
    auto* bytes = static_cast<uint8_t*>(context);
    auto active = [&]() { return rage::load_ptr32<TransitionState>(context, 8); };
    void* next = target;
    do {
        auto* up = parent(next);
        *reinterpret_cast<rage::ptr32<void>*>(up + 0x0C) = next;
        next = up;
    } while (next != active());
    auto enterChild = [&]() {
        void* child = rage::load_ptr32<void>(active(), 0x0C);
        *reinterpret_cast<rage::ptr32<void>*>(bytes + 8) = child;
        const char* name = active()->GetName();
        char scratch[80];
        nop_8240E6D0(scratch, "Entering: %s", name);
        active()->Enter();
        void* node = active()->GetNotificationNode();
        snSession_DD10_w(context, node);
    };
    while (active() != target) enterChild();
    for (;;) {
        auto* previous = active();
        const int32_t status = previous->GetStatus();
        if (status == 1 && rage::load_ptr32<void>(active(), 0x0C)) {
            enterChild();
            if (previous != active()) continue;
        } else {
            const uint32_t savedLimit = *reinterpret_cast<uint32_t*>(bytes + 0x58);
            *reinterpret_cast<uint32_t*>(bytes + 0x58) = *reinterpret_cast<uint32_t*>(bytes + 0x54);
            active()->Update();
            *reinterpret_cast<uint32_t*>(bytes + 0x58) = savedLimit;
        }
        --*reinterpret_cast<uint32_t*>(bytes + 0x54);
        return;
    }
}

namespace rage::snSession_States {
// @ 0x823EDD10 | size: 0xA4
void snSession_InsertConnectionNode(snSessionData* context, snListNode* node) {
    auto* link = reinterpret_cast<ConnectionLink*>(node);
    if (!link || !(link->flags & 0x80)) return;
    auto* list = reinterpret_cast<ConnectionList*>(reinterpret_cast<uint8_t*>(context) + 0x5C);
    if (list->head) {
        auto* previous = list->tail.get();
        auto* next = previous->next.get();
        link->next = next;
        if (next) next->previous = link;
        else list->tail = link;
        previous->next = link;
        link->previous = previous;
    } else {
        list->head = link;
        list->tail = link;
        link->next = nullptr;
        link->previous = nullptr;
    }
    ++list->count;
    link->flags &= 0x7F;
}

// @ 0x823EDDB8 | size: 0xA8
void snSession_RemoveConnectionNode(snSessionData* context, snListNode* node) {
    auto* link = reinterpret_cast<ConnectionLink*>(node);
    if (!link || (link->flags & 0x80)) return;
    auto* list = reinterpret_cast<ConnectionList*>(reinterpret_cast<uint8_t*>(context) + 0x5C);
    auto* previous = link->previous.get();
    auto* next = link->next.get();
    if (!previous) {
        list->head = next;
        if (next) next->previous = nullptr;
        else list->tail = nullptr;
    } else {
        previous->next = next;
        if (next) next->previous = previous;
        else list->tail = previous;
    }
    link->next = nullptr;
    link->previous = nullptr;
    --list->count;
    link->flags |= 0x80;
}
}
