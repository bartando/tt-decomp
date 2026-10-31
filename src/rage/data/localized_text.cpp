#include "rage/localized_text.hpp"
#include <cstddef>
#include <cstring>

extern "C" void* rage_Alloc(uint32_t bytes); // @ 0x820DEC88
extern void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0
extern void* localizedFontCreate(const char* name); // @ 0x82409128

static_assert(sizeof(LocalizedText) == 0x18, "localized text layout");
static_assert(sizeof(LocalizedTextNode) == 0x0C, "text hash node layout");

// @ 0x824090D0 | size: 0x54
uint32_t localizedTextHash(const char* key) {
    uint32_t hash = 0;
    while (const int8_t character = static_cast<int8_t>(*key++)) {
        hash = hash * 16 + static_cast<uint32_t>(character);
        const uint32_t high = hash & 0xF0000000u;
        if (high) hash ^= high ^ (high >> 24);
    }
    return hash;
}

// @ 0x82433748 | size: 0x24
uint32_t localizedWideLength(const uint16_t* text) {
    const uint16_t* end = text;
    while (*end) ++end;
    return static_cast<uint32_t>(end - text);
}

// @ 0x82427E50 | size: 0x6C
uint16_t* localizedWideDuplicate(const uint16_t* text) {
    if (!text) return nullptr;
    const uint32_t count = localizedWideLength(text) + 1;
    auto* copy = static_cast<uint16_t*>(rage_Alloc(count > 0x7FFFFFFFu ? UINT32_MAX : count * 2));
    return static_cast<uint16_t*>(std::memmove(copy, text, count * 2));
}

// @ 0x8240A498 | size: 0xD8
bool localizedTextInsert(LocalizedTextTable* table, uint32_t hash, LocalizedText* text) {
    const uint32_t bucket = hash % table->bucketCount;
    auto* node = table->buckets.get()[bucket].get();
    while (node) {
        if (node->hash == hash) return false;
        node = node->next.get();
    }
    auto* added = static_cast<LocalizedTextNode*>(rage_Alloc(sizeof(LocalizedTextNode)));
    if (added) {
        added->hash = hash;
        added->value = text;
        added->next = table->buckets.get()[hash % table->bucketCount].get();
    }
    // Allocation failure faults in retail when it links the new node as well.
    added->next = table->buckets.get()[bucket].get();
    table->buckets.get()[bucket] = added;
    ++table->count;
    return true;
}

// @ 0x82408F08 | size: 0x1C8
LocalizedText* localizedTextLookup(void* /*context*/, const char* key) {
    auto* table = g_localizationTable.get();
    if (!table) {
        nop_8240E6D0("Must call STRINGTABLE.Init() or STRINGTABLE.Load() before txtStringTable::Get()");
        return nullptr;
    }
    const uint32_t hash = localizedTextHash(key);
    auto* node = table->buckets.get()[hash % table->bucketCount].get();
    LocalizedText* text = nullptr;
    while (node) {
        if (node->hash == hash) {
            text = node->value.get();
            break;
        }
        node = node->next.get();
    }
    if (text) return text;
    nop_8240E6D0("String '%s' not in stringtable (creating temporary entry).", key);
    uint16_t* fallback = nullptr;
    if (key) {
        const size_t count = std::strlen(key) + 1;
        fallback = static_cast<uint16_t*>(__builtin_alloca(count * 2));
        for (size_t i = 0; i < count; ++i) fallback[i] = static_cast<uint8_t>(key[i]);
    }
    text = static_cast<LocalizedText*>(rage_Alloc(sizeof(LocalizedText)));
    if (text) {
        text->hash = 0;
        text->font = nullptr;
        text->text = nullptr;
        text->scaleX = 1.0f;
        text->scaleY = 1.0f;
        text->field14 = 0;
        text->field15 = 0;
        text->field16 = 1;
    }
    const uint16_t* copy = localizedWideDuplicate(fallback);
    text->text = copy;
    text->hash = localizedTextHash(key);
    if (g_localizationDefaultFontName) {
        text->font = localizedFontCreate(g_localizationDefaultFontName.get());
    }
    localizedTextInsert(g_localizationTable.get(), text->hash, text);
    return text;
}

// @ 0x82228990 | size: 0x15C
extern "C" void rage_atStringCopy(const char* key, char* destination, int capacity) {
    const uint16_t* text = localizedTextLookup(&g_localizationTable, key)->text.get();
    uint32_t written = 0;
    const uint32_t limit = static_cast<uint32_t>(capacity);
    while (written < limit && *text) {
        const uint16_t character = *text;
        char encoded[3];
        uint32_t count;
        if (character < 0x80) {
            encoded[0] = static_cast<char>(character);
            count = 1;
        } else if (character < 0x800) {
            encoded[0] = static_cast<char>(0xC0 | (character >> 6));
            encoded[1] = static_cast<char>(0x80 | (character & 0x3F));
            count = 2;
        } else {
            encoded[0] = static_cast<char>(0xE0 | (character >> 12));
            encoded[1] = static_cast<char>(0x80 | ((character >> 6) & 0x3F));
            encoded[2] = static_cast<char>(0x80 | (character & 0x3F));
            count = 3;
        }
        if (written + count >= limit) break;
        std::memcpy(destination + written, encoded, count);
        written += count;
        ++text;
    }
    // Retail writes this terminator even when capacity is zero.
    destination[written] = 0;
    for (uint32_t i = 0; i < limit; ++i) {
        const int8_t character = static_cast<int8_t>(destination[i]);
        if (character == 0x1C || character == 0x1D) destination[i] = '"';
        else if (character == '\n') destination[i] = '\r';
        else if (character == 0) break;
    }
}
