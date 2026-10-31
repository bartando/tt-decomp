#include <cstdint>

struct fxBallSplash2D;

// Two 0x50-byte splash records follow the 0x20-byte object header. Only the
// active byte and the original scalar fields are reset; padding stays intact.
// @ 0x82389BD8 | size: 0x74
void fxBallSplash2D_ResetSplashes(fxBallSplash2D* object) {
    auto* bytes = reinterpret_cast<uint8_t*>(object);
    constexpr unsigned zeroFields[] = {0x04u, 0x0Cu, 0x14u, 0x1Cu, 0x30u, 0x40u, 0x44u, 0x48u};
    constexpr unsigned lowerBounds[] = {0x08u, 0x10u, 0x18u, 0x20u, 0x34u};
    for (unsigned i = 0; i < 2; ++i) {
        auto* record = bytes + 0x20 + i * 0x50;
        record[0] = 0;
        for (unsigned offset : zeroFields)
            *reinterpret_cast<float*>(record + offset) = 0.0f;
        for (unsigned offset : lowerBounds)
            *reinterpret_cast<float*>(record + offset) = -1000.0f;
        *reinterpret_cast<float*>(record + 0x38) = 1000.0f;
    }
}
