#include "rage/swf.hpp"
#include "rage/ptr32.hpp"
#include <cstdint>

namespace rage {
extern const float g_swfTwipsToPixels; // @ 0x820290F0
}

extern "C" {
float util_EF98(void* instance, float* outMin); // @ 0x823FEF98
float swfINSTANCE_F0D8_w(void* instance, float* outMin); // @ 0x823FF0D8
}

namespace {
struct BoundsInstance {
    rage::ptr32<void> dispatch;
    rage::ptr32<rage::swfOBJECT> definition;
    uint8_t _pad08[0xAC];
    rage::ptr32<BoundsInstance> firstChild;
    rage::ptr32<BoundsInstance> nextSibling;
};
static_assert(sizeof(BoundsInstance) == 0xBC);

float extent(BoundsInstance* instance, float* outMin, unsigned axis) {
    constexpr float emptyMin = 0x1.fffffep+127f;
    constexpr float emptyMax = -0x1.fffffep+127f;
    float minimum = emptyMin;
    float maximum = emptyMax;
    const int32_t* bounds = instance->definition->GetBounds();
    if (bounds) {
        // The subtraction wraps as a 32-bit word before signed conversion.
        const int32_t width = static_cast<int32_t>(static_cast<uint32_t>(bounds[axis + 2]) -
                                                   static_cast<uint32_t>(bounds[axis]));
        const float lower = static_cast<float>(bounds[axis]) * rage::g_swfTwipsToPixels;
        const float span = static_cast<float>(width) * rage::g_swfTwipsToPixels;
        const float upper = lower + span;
        if (lower < minimum) minimum = lower;
        if (upper > maximum) maximum = upper;
    }
    for (auto* child = instance->firstChild.get(); child; child = child->nextSibling.get()) {
        float childMin;
        // Both retail routines call the width helper for children.
        const float childWidth = util_EF98(child, &childMin);
        if (childMin < minimum) minimum = childMin;
        const float childMax = childMin + childWidth;
        if (childMax > maximum) maximum = childMax;
    }
    if (minimum == emptyMin || maximum == emptyMax) return 0.0f;
    if (outMin) *outMin = minimum;
    return maximum - minimum;
}
}

// @ 0x823FEF98
extern "C" float util_EF98(void* instance, float* outMin) {
    return extent(static_cast<BoundsInstance*>(instance), outMin, 0);
}

// @ 0x823FF0D8
extern "C" float swfINSTANCE_F0D8_w(void* instance, float* outMin) {
    return extent(static_cast<BoundsInstance*>(instance), outMin, 1);
}
