// Spin settings and table-relative spin conversion, recovered from the PPC.
#include <cstdint>

namespace {
template<class T> const T& at(const void* object, unsigned offset) {
    return *reinterpret_cast<const T*>(static_cast<const uint8_t*>(object) + offset);
}
}

// Direction 3 shares direction 2's settings. Unknown directions always use the
// default at +0x10, even for a special shot or one with a type-specific row.
// @ 0x8220E1B0 | size: 0x174
float util_E1B0(void* settings, uint32_t direction, int32_t shotType, uint8_t special) {
    if (direction > 3) return at<float>(settings, 0x10);
    unsigned row = 0x10;
    if (special) row = 0x34;
    else if (shotType == 10) row = 0x28;
    else if (shotType == 9 || shotType == 8) row = 0x1C;
    const unsigned column = direction == 3 ? 2 : direction;
    return at<float>(settings, row + column * 4);
}
