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

extern void* g_swfNodePool; // @ 0x82604C5C

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
    auto* pool = static_cast<SwfNodePool*>(g_swfNodePool);
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

extern void* g_swfMemberNodePool; // @ 0x82604C54
extern uint32_t g_swfPriorityMemberNames[13]; // @ 0x825C2D30
extern uint32_t g_swfPriorityMemberHashes[13]; // @ 0x82604CE8
extern uint8_t g_swfPriorityMemberHashesReady; // @ 0x826066C8

uint32_t* swfFindMember(void* list, const char* name); // @ 0x823FB3B8
// @ 0x8223A868
uint32_t swfHashMemberName(const char* name) {
    uint32_t hash = 0;
    while (*name) {
        int32_t ch = static_cast<int8_t>(*name++);
        if (ch >= 'a' && ch <= 'z') ch -= 32;
        hash = (hash << 4) + ch;
        uint32_t high = hash & 0xF0000000u;
        hash ^= high ^ (high >> 24);
    }
    return hash;
}

// Set the two-word value, inserting a pooled node if its name hash is absent.
// Priority hashes go at the head; other new members go at the tail.
// @ 0x823FB258
void swfSetMember(void* list, const char* name, const uint32_t* value) {
    auto* existing = swfFindMember(list, name);
    if (existing != nullptr) {
        existing[0] = value[0];
        existing[1] = value[1];
        return;
    }

    auto* pool = static_cast<SwfNodePool*>(g_swfMemberNodePool);
    const uint32_t node = pool->freeHead;
    const uint32_t nextFree = *at<uint32_t>(node);
    --pool->freeCount;
    pool->freeHead = nextFree;
    if (node != 0) {
        auto* fields = at<uint32_t>(node);
        fields[0] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(name));
        fields[1] = value[0];
        fields[3] = 0;
        fields[2] = value[1];
        fields[4] = swfHashMemberName(name);
    }

    auto* ends = static_cast<uint32_t*>(list);
    if (ends[0] == 0) {
        ends[1] = node;
        ends[0] = node;
        return;
    }
    if (!g_swfPriorityMemberHashesReady) {
        for (int i = 0; i < 13; ++i) {
            g_swfPriorityMemberHashes[i] = swfHashMemberName(at<const char>(g_swfPriorityMemberNames[i]));
        }
        g_swfPriorityMemberHashesReady = 1;
    }
    const uint32_t hash = at<uint32_t>(node)[4];
    for (int i = 0; i < 13; ++i) {
        if (hash == g_swfPriorityMemberHashes[i]) {
            at<uint32_t>(node)[3] = ends[0];
            ends[0] = node;
            return;
        }
    }
    at<uint32_t>(ends[1])[3] = node;
    ends[1] = node;
}
