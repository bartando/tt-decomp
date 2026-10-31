#include <cstdint>

// These legacy msgMsgSink names belong to the packed image descriptor at
// 0x82451B98. Bit 0 of word 1 selects its packed representation.

// @ 0x82451D30 | size: 0x50
uint32_t msgMsgSink_1D30_g(void* descriptor) {
    const auto* words = static_cast<const uint32_t*>(descriptor);
    return (words[1] & 1u) ? ((words[4] >> 3) & 0x1FFFF800u) : words[4];
}

// @ 0x82451D80 | size: 0x68
uint32_t msgMsgSink_1D80_g(void* descriptor) {
    const auto* words = static_cast<const uint32_t*>(descriptor);
    const uint32_t size = (words[1] & 1u)
        ? (((words[4] >> 3) - 1u) & 0xFFFFF800u) + 0x800u
        : words[5];
    return size == 0 ? words[3] : size;
}
