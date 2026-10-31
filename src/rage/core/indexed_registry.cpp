#include "rage/indexed_registry.h"

namespace {
struct RegistryNode {
    uint8_t _pad00[8];
    RegistryNode* next;             // +0x08
};

struct RegistryList {
    uint8_t _pad00[0x0C];
    RegistryNode* first;            // +0x0C
};

struct Registry {
    uint8_t _pad00[8];
    RegistryList* children;         // +0x08
};
}

// @ 0x821DC2A0
extern "C" void* pg_C2A0_g(void* registry, uint32_t index) {
    RegistryNode* node = static_cast<Registry*>(registry)->children->first;
    while (node != nullptr && index != 0) {
        --index;
        node = node->next;
    }
    return node;
}
