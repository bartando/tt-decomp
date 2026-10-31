#include "rage/operator_new.hpp"
#include "rage/atSingleton.hpp"
#include "rage/singleton.h"

extern void* rage_strDuplicate(const char* text);  // @ 0x820C29E0
struct xmlTreeEntry;
extern void* xmlTreeEntry_DeleteArray(xmlTreeEntry* entries);  // @ 0x820C2980
extern "C" void* g_sda_base;

namespace rage {

// @ 0x821A8588 | size: 0x190
SingletonEntry* InitializeSingleton(SingletonArray* array) {
    if (array->count == array->capacity) {
        array->capacity = static_cast<uint16_t>(array->capacity + 16);
        const uint32_t capacity = array->capacity;
        auto* block = static_cast<uint32_t*>(::rage_Alloc(capacity * sizeof(SingletonEntry) + 4));
        SingletonEntry* entries = nullptr;
        if (block) {
            *block = capacity;
            entries = reinterpret_cast<SingletonEntry*>(block + 1);
            for (uint32_t i = 0; i < capacity; ++i) {
                entries[i].name = nullptr;
                entries[i].instance = nullptr;
            }
        }

        for (uint16_t i = 0; i < array->count; ++i) {
            auto* name = static_cast<char*>(rage_strDuplicate(array->entries[i].name));
            const char* oldName = entries[i].name;
            if (oldName && (rage_FindSingleton(const_cast<char*>(oldName)) & 0xFF) == 0) {
                auto* thread = *static_cast<void***>(g_sda_base);
                void* allocator = thread[1];
                auto** vtable = *static_cast<void***>(allocator);
                reinterpret_cast<void (*)(void*, const char*)>(vtable[2])(allocator, oldName);
            }
            entries[i].name = name;
            entries[i].hash = array->entries[i].hash;
            entries[i].instance = array->entries[i].instance;
        }
        // The delete[] helper ignores the original r4 = 3 argument.
        if (array->entries)
            xmlTreeEntry_DeleteArray(reinterpret_cast<xmlTreeEntry*>(array->entries));
        array->entries = entries;
    }
    SingletonEntry* slot = array->entries + array->count;
    array->count = static_cast<uint16_t>(array->count + 1);
    return slot;
}

} // namespace rage
