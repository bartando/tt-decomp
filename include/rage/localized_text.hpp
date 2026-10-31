#pragma once
#include "rage/ptr32.hpp"
#include <cstdint>

struct LocalizedText {
    uint32_t hash;
    rage::ptr32<void> font;
    rage::ptr32<const uint16_t> text;
    float scaleX, scaleY;
    uint8_t field14, field15;
    uint16_t field16;
};
struct LocalizedTextNode {
    uint32_t hash;
    rage::ptr32<LocalizedText> value;
    rage::ptr32<LocalizedTextNode> next;
};
struct LocalizedTextTable {
    uint32_t bucketCount;
    rage::ptr32<rage::ptr32<LocalizedTextNode>> buckets;
    uint32_t count;
};
extern rage::ptr32<LocalizedTextTable> g_localizationTable; // @ 0x82715FA0
extern rage::ptr32<const char> g_localizationDefaultFontName; // @ 0x826066DC
uint32_t localizedTextHash(const char* key); // @ 0x824090D0
LocalizedText* localizedTextLookup(void* context, const char* key); // @ 0x82408F08
bool localizedTextInsert(LocalizedTextTable* table, uint32_t hash, LocalizedText* text); // @ 0x8240A498
uint32_t localizedWideLength(const uint16_t* text); // @ 0x82433748
uint16_t* localizedWideDuplicate(const uint16_t* text); // @ 0x82427E50
extern "C" void rage_atStringCopy(const char* key, char* destination, int capacity); // @ 0x82228990
