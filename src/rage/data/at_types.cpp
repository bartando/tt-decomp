/**
 * at_types.cpp — RAGE at* / datRef / datResource / datArray bridging stubs
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Consolidation target for the proto-RAGE `at*` (array-template) family
 * surface that the rest of the tree calls but for which the original
 * template expansion has not yet been individually decompiled.
 *
 * Real, address-backed lifts that share these names live in:
 *   - src/rage/memory/atArray.cpp       (atArray_Destructor @ 0x820C2980)
 *   - src/rage/memory/atSingleton.cpp   (atSingleton_CAD0_g, ..._Find_90D0,
 *                                        ..._23C0, numbered variants)
 *   - src/rage/memory/rage_memory.cpp   (atSingleton_0128_wrh, _2038, _23C0,
 *                                        datArray_Grow sites)
 *   - src/rage/misc/rage_at.cpp         (atSingleton_23C0 bit-stream helper)
 *
 * Those files are not part of the active CMake `SOURCES` set in this tree,
 * so the functions below continue to provide the weak-body linker surface
 * every other translation unit needs. As soon as the above files are added
 * to CMakeLists.txt, the address-backed versions supersede these and this
 * file can be emptied.
 *
 * Most symbols here remain thin bridges. Where the binary body is fully
 * recovered and the active build still routes through this file, we keep a
 * concrete implementation here so callers stop depending on stubs.cpp.
 */

#include <cstdint>
#include <cstring>

namespace {

uint32_t ComputeHashString(const char* text)
{
    if (text == nullptr) {
        return 0;
    }

    uint32_t hash = 0;
    while (*text != '\0') {
        hash = (hash << 4) + static_cast<uint8_t>(*text++);

        const uint32_t highBits = hash & 0xF0000000;
        if (highBits != 0) {
            hash ^= (highBits >> 24);
            hash ^= highBits;
        }
    }

    return hash;
}

bool StringsMatch(const char* left, const char* right)
{
    if (left == right) {
        return true;
    }

    if (left == nullptr || right == nullptr) {
        return false;
    }

    while (*left != '\0' && *left == *right) {
        ++left;
        ++right;
    }

    return *left == *right;
}

} // namespace

// ─────────────────────────────────────────────────────────────────────────────
// rage::xmlTree teardown. Callers know 0x821A8070 as atArray_Clear; it is the
// xmlTree destructor body (vtable 0x8203A928, back to datBase 0x820276C4 at the end).
// rage_core_utils.cpp aliases it to the C symbol _atArray_Clear.
// ─────────────────────────────────────────────────────────────────────────────

void rage_free(void* p);

struct xmlTreeListNode {
    void** vtable;              // slot 0: scalar deleting destructor
    uint32_t _4;
    xmlTreeListNode* next;      // +0x08
};

struct xmlTreeEntry {           // 12 bytes on the game
    char* name;                 // +0x00
    uint32_t _4;
    xmlTreeListNode* head;      // +0x08
};

struct xmlTreeView {
    void** vtable;
    xmlTreeListNode* root;      // +0x04
    xmlTreeEntry* entries;      // +0x08, new[]'d with a count word in front
    uint16_t count;             // +0x0C
    uint16_t capacity;          // +0x0E
};

namespace {

using ScalarDtorFn = void (*)(void*, int);

constexpr uintptr_t kVtable_xmlTree = 0x8203A928;
constexpr uintptr_t kVtable_datBase = 0x820276C4;

} // namespace

// @ 0x821A8118
void xmlTreeEntry_Destruct(xmlTreeEntry* entry)
{
    for (xmlTreeListNode* node = entry->head; node != nullptr;) {
        xmlTreeListNode* next = node->next;
        reinterpret_cast<ScalarDtorFn>(node->vtable[0])(node, 1);
        node = next;
    }
    rage_free(entry->name);
}

// delete[] for xmlTreeEntry; the flags argument in r4 is ignored.
// @ 0x820C2980
void* xmlTreeEntry_DeleteArray(xmlTreeEntry* entries)
{
    uint32_t* block = reinterpret_cast<uint32_t*>(entries) - 1;
    for (int32_t i = static_cast<int32_t>(*block) - 1; i >= 0; --i) {
        xmlTreeEntry_Destruct(&entries[i]);
    }
    rage_free(block);
    return block;
}

// @ 0x821A8070
void atArray_Clear(void* obj)
{
    auto* tree = static_cast<xmlTreeView*>(obj);
    tree->vtable = reinterpret_cast<void**>(kVtable_xmlTree);
    if (tree->root != nullptr) {
        reinterpret_cast<ScalarDtorFn>(tree->root->vtable[0])(tree->root, 1);
    }
    if (tree->entries != nullptr) {
        xmlTreeEntry_DeleteArray(tree->entries);
    }
    tree->entries = nullptr;
    tree->count = 0;
    tree->capacity = 0;
    tree->vtable = reinterpret_cast<void**>(kVtable_datBase);
}

// ─────────────────────────────────────────────────────────────────────────────
// atArray<u32>::Realloc. The original inlines rage_free.
// ─────────────────────────────────────────────────────────────────────────────

extern "C" void* xe_EC88(uint32_t size);  // operator new

struct atArrayU32View {
    uint32_t* data;     // +0x00
    int32_t count;      // +0x04
    int32_t capacity;   // +0x08
};

// @ 0x821322B0
void* datArray_Grow(void* obj, uint32_t newCapacity)
{
    auto* array = static_cast<atArrayU32View*>(obj);
    const int32_t capacity = static_cast<int32_t>(newCapacity);
    uint32_t* data = nullptr;
    if (capacity > 0) {
        data = static_cast<uint32_t*>(
            xe_EC88(newCapacity > 0x3FFFFFFFu ? 0xFFFFFFFFu : newCapacity * 4));
    }
    const int32_t keep = capacity < array->count ? capacity : array->count;
    for (int32_t i = 0; i < keep; ++i) {
        data[i] = array->data[i];
    }
    uint32_t* old = array->data;
    array->capacity = capacity;
    array->count = keep;
    if (old != nullptr) {
        rage_free(old);
    }
    array->data = data;
    return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// String duplication and the 16-byte registry entries (name + three words)
// appended through atSingletonPool_AllocEntry.
// ─────────────────────────────────────────────────────────────────────────────

// @ 0x820C29E0
void* rage_strDuplicate(const char* text)
{
    if (text == nullptr) {
        return nullptr;
    }
    uint32_t size = 0;
    while (text[size] != '\0') {
        ++size;
    }
    ++size;
    void* copy = xe_EC88(size);
    return memcpy(copy, text, size);
}

extern "C" void* rage_strDuplicate_c(const char* text) __asm__("_rage_strDuplicate");
extern "C" void* rage_strDuplicate_c(const char* text) { return rage_strDuplicate(text); }

struct atRegistryEntry {
    char* name;
    uint32_t value4;
    uint32_t value8;
    uint32_t valueC;
};

struct atRegistryPool {
    atRegistryEntry* data;
    uint16_t count;
    uint16_t capacity;
};

// @ 0x82618550
extern atRegistryPool g_atRegistryPool;

// delete[] for atRegistryEntry (the original inlines rage_free for each name).
// @ 0x821A9370
void* atRegistryEntry_DeleteArray(atRegistryEntry* entries)
{
    uint32_t* block = reinterpret_cast<uint32_t*>(entries) - 1;
    for (int32_t i = static_cast<int32_t>(*block) - 1; i >= 0; --i) {
        if (entries[i].name != nullptr) {
            rage_free(entries[i].name);
        }
    }
    rage_free(block);
    return block;
}

// Appends a slot to the global registry, growing it by 16. Callers pass an
// argument the original never reads.
// @ 0x821A91E0
void* atSingletonPool_AllocEntry(uint32_t /*unused*/)
{
    atRegistryPool& pool = g_atRegistryPool;
    if (pool.count == pool.capacity) {
        const uint16_t capacity = static_cast<uint16_t>(pool.capacity + 16);
        pool.capacity = capacity;
        atRegistryEntry* fresh = nullptr;
        uint32_t* block = static_cast<uint32_t*>(xe_EC88(capacity * 16u + 4));
        if (block != nullptr) {
            block[0] = capacity;
            fresh = reinterpret_cast<atRegistryEntry*>(block + 1);
            for (uint32_t i = 0; i < capacity; ++i) {
                fresh[i].name = nullptr;
            }
        }
        for (uint16_t i = 0; i < pool.count; ++i) {
            atRegistryEntry& src = pool.data[i];
            atRegistryEntry& dst = fresh[i];
            char* name = static_cast<char*>(rage_strDuplicate(src.name));
            if (dst.name != nullptr) {
                rage_free(dst.name);
            }
            dst.name = name;
            dst.value4 = src.value4;
            dst.value8 = src.value8;
            dst.valueC = src.valueC;
        }
        if (pool.data != nullptr) {
            atRegistryEntry_DeleteArray(pool.data);
        }
        pool.data = fresh;
    }
    const uint16_t index = pool.count;
    pool.count = static_cast<uint16_t>(index + 1);
    return &pool.data[index];
}

// All symbols below use C linkage — C source files (src/rage/core/app_init.c,
// src/rage/render_loop.c, src/xam/*) reach them through underscore-prefixed
// symbol names. C++ callers just take the unmangled name.
extern "C" {

// ─────────────────────────────────────────────────────────────────────────────
// atHashMap — hash-bucketed container surface.
// atHashMap_Clear  @ rage_C0E0 (~0x8234C0E0, caller: pongCreatureType dtor).
// atHashMap_Find   — name-keyed lookup invoked by rage_par.cpp and several
//                    animation blend-clip caches (pcr_anim_blenders.cpp).
// ─────────────────────────────────────────────────────────────────────────────
void atHashMap_Clear(void* container) { (void)container; }
void* atHashMap_Find(void* table, const void* key) {
    if (table == nullptr) {
        return nullptr;
    }

    const char* searchKey = static_cast<const char*>(key);
    const uint16_t bucketCount = *reinterpret_cast<uint16_t*>(
        static_cast<uint8_t*>(table) + 4);
    if (bucketCount == 0) {
        return nullptr;
    }

    void*** bucketArray = *reinterpret_cast<void****>(table);
    if (bucketArray == nullptr) {
        return nullptr;
    }

    const uint32_t bucketIndex = ComputeHashString(searchKey) % bucketCount;
    void** entry = static_cast<void**>(bucketArray[bucketIndex]);

    while (entry != nullptr) {
        const char* entryKey = static_cast<const char*>(entry[0]);
        if (StringsMatch(searchKey, entryKey)) {
            return static_cast<uint8_t*>(static_cast<void*>(entry)) + 4;
        }

        entry = static_cast<void**>(entry[2]);
    }

    return nullptr;
}

void* atArray_Destructor(void* pArray) { (void)pArray; return nullptr; }

// ─────────────────────────────────────────────────────────────────────────────
// atSingleton — registry/tracker family. Named slots are documented at their
// real lift sites. Duplicates here intentionally kept *very* thin so the
// real ones in rage/memory/atSingleton.cpp (when added to CMakeLists) win.
// ─────────────────────────────────────────────────────────────────────────────
uint8_t atSingleton_Find(void* ptr) {
    // Real: atSingleton_Find_90D0 @ 0x820F90D0 — hashed registry lookup.
    (void)ptr;
    return 0;
}

void atSingleton_Remove(void* singleton) {
    // Real: atSingleton_1C70_fw @ 0x82151C70.
    (void)singleton;
}

void  atSingleton_0128_wrh(void* a, uint32_t b) { (void)a; (void)b; }
void  atSingleton_2038(void* a, uint32_t b)     { (void)a; (void)b; }
void  atSingleton_23C0(void* a)                 { (void)a; }
void  atSingleton_29E8_p25(void* a)             { (void)a; }
void  atSingleton_5CD0_fw(void* a, uint32_t b)  { (void)a; (void)b; }
void  atSingleton_8068_h(void* a)               { (void)a; }
void  atSingleton_8A48_p42(void* a)             { (void)a; }
void  atSingleton_8E88_p42(void* a, void* b, uint32_t c, uint32_t d, uint32_t e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
void* atSingleton_CAD0_g(void* a) { (void)a; return nullptr; }

// atSingleton_QueryEventData — data-query utility invoked by gameplay code;
// confirmed via find_callers to be non-network (no msgMsgSink references).
void atSingleton_QueryEventData(void* a, void* b) { (void)a; (void)b; }

// ─────────────────────────────────────────────────────────────────────────────
// atFactory — singleton-of-factory dispatcher.
//   atFactory_GetFactory: called by fx_effects.cpp and mc_memcard.cpp.
// Real body is in rage/misc/rage_at.cpp (line ~450).
// ─────────────────────────────────────────────────────────────────────────────
void atFactory_GetFactory(void* a) { (void)a; }

// ─────────────────────────────────────────────────────────────────────────────
// datArray / datRef / datResource — data-system helpers.
// datArray_Grow  — bucket expansion on atArray backing storage.
// datRef_Release — reference-count release (real @ rage_6A90 0x82126A90).
// datResource_Load — blocking load dispatch; ph_physics.cpp calls this.
// ─────────────────────────────────────────────────────────────────────────────
void datRef_Release(void* ref)                      { (void)ref; }
void datResource_Load(void* a, const char* b)       { (void)a; (void)b; }

} // extern "C"


// sub_821A8F58 — data registration helper (moved from stubs.cpp)
void sub_821A8F58(void* registry, const char* name, void* data, void* schema, int flags) {
    (void)registry; (void)name; (void)data; (void)schema; (void)flags;
}

