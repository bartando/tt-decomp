// SWF PlaceObject2 clip events: each placed instance keeps a singly linked list of
// nodes pointing at its 12-byte clip-event records. Nodes come from one shared pool.
#include <cstdint>

namespace {

struct SwfListNode {
    uint32_t value;  // the record (32-bit address); the free-list link while pooled
    uint32_t next;
};

struct SwfNodePool {
    uint8_t pad00[6];
    uint16_t freeCount;  // +0x06
    uint8_t pad08[4];
    uint32_t freeHead;   // +0x0C
};

template <typename T>
T* at(uint32_t address) {
    return reinterpret_cast<T*>(static_cast<uintptr_t>(address));
}

} // namespace

extern uint32_t g_swfNodePool; // @ 0x82604C5C

// Replace `instance`'s clip-event list (+0xC8) with one node per record, record 0
// first, and store `events` at +0xC4. The pool is never checked for running dry:
// the original reads the head's link before its null test.
// @ 0x823FD320
void swfSetClipEvents(void* instance, uint32_t events, uint32_t records, int32_t count) {
    if (count <= 0 || records == 0) {
        return;
    }
    auto* fields = static_cast<uint8_t*>(instance);
    auto& list = *reinterpret_cast<uint32_t*>(fields + 0xC8);
    uint32_t node = list;
    list = 0;
    auto* pool = at<SwfNodePool>(g_swfNodePool);
    while (node != 0) {
        auto* released = at<SwfListNode>(node);
        const uint32_t next = released->next;
        released->value = pool->freeHead;
        pool->freeHead = node;
        ++pool->freeCount;
        node = next;
    }

    *reinterpret_cast<uint32_t*>(fields + 0xC4) = events;
    uint32_t record = records + 12u * static_cast<uint32_t>(count - 1);
    for (int32_t i = count - 1; i >= 0; --i, record -= 12) {
        const uint32_t taken = pool->freeHead;
        const uint32_t link = at<SwfListNode>(taken)->value;
        --pool->freeCount;
        pool->freeHead = link;
        if (taken != 0) {
            at<SwfListNode>(taken)->value = record;
            at<SwfListNode>(taken)->next = list;
        }
        list = taken;
    }
}
