#include "game/network_context.hpp"
#include <cstddef>

static_assert(sizeof(void*) != 4 || sizeof(NetworkContextNode) == 24, "pool node layout");
static_assert(sizeof(void*) != 4 || offsetof(NetworkContextPool, activeHead) == 0x4C0, "pool head layout");
static_assert(sizeof(void*) != 4 || offsetof(NetworkContextPool, currentIndex) == 0x6C8, "pool index layout");

// @ 0x823D2E00 | size: 0x88
void networkContextReleaseNode(NetworkContextPool* pool, NetworkContextNode* node) {
    const uint16_t index = static_cast<uint16_t>(node - pool->nodes);
    --pool->activeCount;
    node->field_00 = -1;
    node->field_04 = -1;
    node->activeNext = nullptr;
    node->nextFree = pool->freeTail;
    if (pool->freeTail != UINT16_MAX) {
        pool->nodes[pool->freeTail].previousFree = index;
    }
    pool->freeTail = index;
    ++pool->freeCount;
}

// @ 0x823D2BE8 | size: 0x60
void UpdateNetworkState(void* component) {
    auto* pool = static_cast<NetworkContextPool*>(component);
    while (pool->activeHead != nullptr) {
        NetworkContextNode* node = pool->activeHead;
        pool->activeHead = node->activeNext;
        networkContextReleaseNode(pool, node);
    }
    pool->activeCount = 0;
    pool->field_4CC = 0;
    pool->field_4CE = 0;
    pool->currentIndex = UINT16_MAX;
    pool->field_4C4 = 0;
}
