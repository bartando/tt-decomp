#include "template_registry.hpp"

/**
 * game_94F0 @ 0x820F94F0 | size: 0xA4
 * 
 * Searches the global registry for an interval containing the key pair.
 * 
 * @param registry Unused; the original uses the global registry
 * @param searchKey Pointer to 8-byte key pair to search for
 * @return Index of containing entry, or -1 if not found
 */
int32_t game_94F0(TemplateRegistry* registry, const uint32_t* searchKey) {
    (void)registry;  // The original always searches the global registry.
    int32_t high = static_cast<int32_t>(g_templateRegistry.count - 1);
    int32_t low = 0;
    while (low <= high) {
        int32_t mid = (low + high) >> 1;
        const TemplateRegistryEntry& entry = g_templateRegistry.entries[mid];
        if (searchKey[0] >= entry.field1 && searchKey[1] <= entry.field2)
            return mid;
        if (searchKey[1] < entry.field1)
            high = mid - 1;
        else
            low = mid + 1;
    }
    return -1;
}

