#include "rage/index_wrap.hpp"

// Inclusive signed range. The PPC performs wrapping word arithmetic before
// its signed remainder, including when the range length overflows.
// @ 0x820DC4E8 | size: 0x58
int32_t math_WrapIndex(int32_t value, int32_t minimum, int32_t maximum) {
    if (maximum == minimum) return minimum;
    if (maximum < minimum) return value;
    const uint32_t first = static_cast<uint32_t>(minimum);
    const uint32_t last = static_cast<uint32_t>(maximum);
    const int32_t length = static_cast<int32_t>(last - first + 1u);
    const int32_t offset = static_cast<int32_t>(static_cast<uint32_t>(value) - first);
    if (length == 0 || (offset == INT32_MIN && length == -1)) __builtin_trap();
    const uint32_t origin = value < minimum ? last + 1u : first;
    return static_cast<int32_t>(origin + static_cast<uint32_t>(offset % length));
}
