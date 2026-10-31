// Spin settings and table-relative spin conversion, recovered from the PPC.
#include <cstdint>
#include <cmath>

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

extern "C" void* g_pTableDims; // @ 0x8271A304
extern "C" float g_phCapsuleShapeK; // @ 0x825C8080
extern "C" const float lbl_825CB7C0[4]; // @ 0x825CB7C0
extern "C" const float lbl_825CB7D0[4]; // @ 0x825CB7D0
extern "C" const float lbl_82619BF0[4]; // @ 0x82619BF0
extern "C" const float lbl_82606750[4]; // @ 0x82606750
extern "C" float phBoundCapsule_DD20_fw(float); // @ 0x8227DD20

namespace {
struct SpinVector { float lane[4]; };

float flushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}
float vmxMultiply(float a, float b) {
    return flushVmx(flushVmx(a) * flushVmx(b));
}
float vmxAdd(float a, float b) {
    return flushVmx(flushVmx(a) + flushVmx(b));
}
float vmxSubtract(float a, float b) {
    return flushVmx(flushVmx(a) - flushVmx(b));
}
float dot3(const SpinVector& a, const SpinVector& b) {
    double sum = 0.0;
    for (unsigned lane = 0; lane < 3; ++lane)
        sum += double(flushVmx(a.lane[lane])) * double(flushVmx(b.lane[lane]));
    return flushVmx(static_cast<float>(sum));
}
SpinVector normalize3(const SpinVector& vector) {
    const float squareLength = dot3(vector, vector);
    // Refine the reciprocal-square-root estimate with the original Newton step.
    const float estimate = flushVmx(static_cast<float>(1.0 / std::sqrt(double(squareLength))));
    SpinVector result;
    for (unsigned lane = 0; lane < 4; ++lane) {
        const float y = estimate == flushVmx(lbl_82619BF0[lane])
            ? lbl_82606750[lane] : estimate;
        const float square = vmxMultiply(y, y);
        const float halfEstimate = vmxMultiply(lbl_825CB7D0[lane], y);
        const float error = -vmxSubtract(vmxMultiply(squareLength, square), lbl_825CB7C0[lane]);
        const float scale = vmxAdd(vmxMultiply(error, halfEstimate), y);
        result.lane[lane] = vmxMultiply(vector.lane[lane], scale);
    }
    return result;
}
}

// Reorient a local horizontal spin component across the shot's horizontal
// flight direction, retaining the vertical component. The angle helper call
// is present in the original even though its result is unused here.
// @ 0x82282E70 | size: 0x270
void phBoundCapsule_2E70_fw(void* hit, float* spin) {
    const SpinVector source = at<SpinVector>(hit, 0x60);
    const SpinVector target = at<SpinVector>(hit, 0x20);
    const bool positiveSide = source.lane[2] > 0.0f;
    SpinVector delta;
    for (unsigned lane = 0; lane < 4; ++lane)
        delta.lane[lane] = vmxSubtract(target.lane[lane], source.lane[lane]);
    delta.lane[1] = 0.0f;

    const float endZ = at<float>(g_pTableDims, 0x18) * g_phCapsuleShapeK;
    const float height = at<float>(g_pTableDims, 0x14);
    const SpinVector nearEnd = {{0.0f, height, endZ, 0.0f}};
    const SpinVector farEnd = {{0.0f, height, -endZ, 0.0f}};
    SpinVector reference;
    for (unsigned lane = 0; lane < 4; ++lane)
        reference.lane[lane] = vmxSubtract(farEnd.lane[lane], nearEnd.lane[lane]);
    const SpinVector direction = normalize3(delta);
    const SpinVector tableDirection = normalize3(reference);
    phBoundCapsule_DD20_fw(dot3(tableDirection, direction));

    // The scratch basis retains the unnormalised difference's w lane.
    const SpinVector up = {{0.0f, 1.0f, 0.0f, delta.lane[3]}};
    constexpr unsigned cyclic[4] = {1, 2, 0, 3};
    constexpr unsigned reverse[4] = {2, 0, 1, 3};
    const float horizontalSpin = spin[0];
    const float verticalSpin = spin[1];
    SpinVector output;
    for (unsigned lane = 0; lane < 4; ++lane) {
        const float first = positiveSide
            ? vmxMultiply(up.lane[reverse[lane]], direction.lane[cyclic[lane]])
            : vmxMultiply(direction.lane[reverse[lane]], up.lane[cyclic[lane]]);
        const float second = positiveSide
            ? vmxMultiply(up.lane[cyclic[lane]], direction.lane[reverse[lane]])
            : vmxMultiply(direction.lane[cyclic[lane]], up.lane[reverse[lane]]);
        const float perpendicular = -vmxSubtract(second, first);
        output.lane[lane] = vmxMultiply(perpendicular, horizontalSpin);
    }
    output.lane[1] = verticalSpin;
    __builtin_memcpy(spin, &output, sizeof output);
}
