// Vertex attribute writes to the Xbox 360's 32-bit vertex-buffer layout.
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

// Partial layout recovered from the attribute accessors around 0x82155B08.
// Addresses stay 32-bit even on a host with 64-bit pointers.
struct PgVertexBuffer {
    uint8_t pad00[0x08];
    uint32_t formatAddress;             // +0x08: first word is the attribute flags
    uint8_t pad0C[0x0C];
    uint32_t stagingAddress;            // +0x18: one vertex's data, no stride (pg_6B20_g)
    uint32_t dataAddress;               // +0x1C: CPU mapping, refreshed by pg_7578_g
    uint8_t pad20[0x03];
    uint8_t normalOffset;               // +0x23
    uint8_t pad24[0x0A];
    uint8_t tangentOffset;              // +0x2E
    uint8_t pad2F[0x39];
    uint32_t normalSize;                // +0x68: bytes for the raw-copy format
    uint8_t pad6C[0x28];
    uint32_t tangentSize;               // +0x94: bytes for the raw-copy format
    uint8_t pad98[0x3C];
    uint32_t stride;                    // +0xD4
    uint8_t padD8;
    uint8_t packedTangent;              // +0xD9
    uint8_t padDA;
    uint8_t mapped;                     // +0xDB
};

static_assert(offsetof(PgVertexBuffer, stagingAddress) == 0x18);
static_assert(offsetof(PgVertexBuffer, normalOffset) == 0x23);
static_assert(offsetof(PgVertexBuffer, tangentOffset) == 0x2E);
static_assert(offsetof(PgVertexBuffer, normalSize) == 0x68);
static_assert(offsetof(PgVertexBuffer, tangentSize) == 0x94);
static_assert(offsetof(PgVertexBuffer, stride) == 0xD4);
static_assert(offsetof(PgVertexBuffer, mapped) == 0xDB);

// Xenon's VMX non-Java mode flushes subnormal inputs/results to signed zero.
// Scalar host/PPC floating-point does not necessarily use that mode.
float vmxFloat(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
    }
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

// vnmsubfp with the constants at 0x82034D60/0x82034D70 encodes a signed integer
// in the low mantissa bits around 3.0f; vpkd3d128 (NORMPACKED32) then
// clamps/extracts 10 bits for xyz and 2 bits for w. `v` is 16-byte aligned.
uint32_t packNormPacked32(const float* v) {
    uint32_t packed = 0;
    for (unsigned k = 0; k < 4; ++k) {
        const float scale = k < 3 ? -511.0f / 4194304.0f : -3.0f / 4194304.0f;
        volatile float product = vmxFloat(v[k]) * scale;
        float encoded = 3.0f - vmxFloat(product);
        const uint32_t minBits = k < 3 ? 0x403FFE01u : 0x40400000u;
        const uint32_t maxBits = k < 3 ? 0x404001FFu : 0x40400003u;
        float minimum, maximum;
        std::memcpy(&minimum, &minBits, sizeof(minimum));
        std::memcpy(&maximum, &maxBits, sizeof(maximum));
        encoded = !(encoded >= minimum) ? minimum : encoded > maximum ? maximum : encoded;
        uint32_t bits;
        std::memcpy(&bits, &encoded, sizeof(bits));
        packed |= (bits & (k < 3 ? 0x3FFu : 3u)) << (10 * k);
    }
    return packed;
}

const float* align16(const float* p) {
    return reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(p) & ~uintptr_t(15));
}

} // namespace

extern "C" uint8_t pg_7578_g(void* buffer); // @ 0x82157578
extern "C" float* util_5B08(float* result, void* buffer, uint32_t index); // @ 0x82155B08

// Static-initialized vectors used by the original's bitwise tangent/sign merge.
extern const float lbl_82619BD0[4]; // @ 0x82619BD0
extern const float lbl_82606750[4]; // @ 0x82606750
extern const uint32_t lbl_82619BE0[4]; // @ 0x82619BE0

// @ 0x82156C00
extern "C" void pg_6C00_w(void* vertexBuffer, uint32_t index, uint32_t /*unused*/,
                          const float* tangent, const float* normal, const float* bitangent) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    auto* format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    if ((*format & 0x4000) == 0) {
        return;
    }
    if (buffer->mapped == 0) {
        pg_7578_g(buffer);
    }

    // The mapping helper may replace both the format and the CPU data pointer.
    format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    const uint32_t offset = buffer->stride * index + buffer->tangentOffset;
    auto* destination = reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(buffer->dataAddress + offset));
    if ((*format & 0x400000) == 0) {
        // lvx/stvx round addresses down to a 16-byte boundary.
        normal = reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(normal) & ~uintptr_t(15));
        tangent = reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(tangent) & ~uintptr_t(15));
        float n[3] = {vmxFloat(normal[0]), vmxFloat(normal[1]), vmxFloat(normal[2])};
        float t[3] = {vmxFloat(tangent[0]), vmxFloat(tangent[1]), vmxFloat(tangent[2])};
        alignas(16) float fetched[4];
        if (bitangent == nullptr) {
            bitangent = util_5B08(fetched, buffer, index);
        }
        bitangent = reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(bitangent) & ~uintptr_t(15));

        // N dot (T cross B). VMX multiplies round before the subtract (not fused).
        // Snapshot N/T before fetching B: the helper can touch the input memory.
        float cross[3];
        for (unsigned k = 0; k < 3; ++k) {
            const unsigned y = (k + 1) % 3, z = (k + 2) % 3;
            volatile float first = vmxFloat(bitangent[z]) * t[y];
            volatile float second = vmxFloat(bitangent[y]) * t[z];
            cross[k] = vmxFloat(vmxFloat(first) - vmxFloat(second));
        }
        // vmsum3fp128 accumulates the products before its single-precision result.
        const float dot = vmxFloat(static_cast<float>(static_cast<double>(n[0]) * cross[0]
                                                   + static_cast<double>(n[1]) * cross[1]
                                                   + static_cast<double>(n[2]) * cross[2]));
        uint32_t result[4];
        // The original reloads T after the helper, then combines raw bits with
        // +sign when dot < 0, -sign otherwise (also for zero and NaN).
        for (unsigned k = 0; k < 4; ++k) {
            uint32_t bits, signBits;
            std::memcpy(&bits, tangent + k, sizeof(bits));
            const float sign = lbl_82606750[k] > dot ? lbl_82619BD0[k] : 0.0f - lbl_82619BD0[k];
            std::memcpy(&signBits, &sign, sizeof(signBits));
            result[k] = (bits & lbl_82619BE0[k]) | signBits;
        }
        destination = reinterpret_cast<uint8_t*>(reinterpret_cast<uintptr_t>(destination) & ~uintptr_t(15));
        std::memcpy(destination, result, sizeof(result));
    } else if (buffer->packedTangent != 0) {
        const uint32_t packed = packNormPacked32(align16(tangent));
        std::memcpy(destination, &packed, sizeof(packed));
    } else {
        // Unlike the vector paths, memcpy uses the exact (possibly unaligned) pointers.
        std::memcpy(destination, tangent, buffer->tangentSize);
    }
}

// @ 0x82156A40
extern "C" void pg_6A40_w(void* vertexBuffer, uint32_t index, const float* normal) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    auto* format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    if ((*format & 0x8) == 0) {
        return;
    }
    if (buffer->mapped == 0) {
        pg_7578_g(buffer);
    }

    format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    const uint32_t offset = buffer->stride * index + buffer->normalOffset;
    auto* destination = reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(buffer->dataAddress + offset));
    // Big-endian halfword at +4 of the format: bits 9-11 hold the normal's type.
    const uint16_t normalType = reinterpret_cast<const uint16_t*>(format)[2];
    if (((normalType >> 9) & 7) == 5) {
        const uint32_t packed = packNormPacked32(align16(normal));
        std::memcpy(destination, &packed, sizeof(packed));
    } else {
        std::memcpy(destination, normal, buffer->normalSize);
    }
}

// Same tangent formats as pg_6C00_w, minus the handedness path, written to the
// staging vertex: the original stores the index argument but never reads it.
// @ 0x82156B20
extern "C" void pg_6B20_g(void* vertexBuffer, uint32_t /*index*/, const float* tangent) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    auto* format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    if ((*format & 0x4000) == 0) {
        return;
    }
    if (buffer->mapped == 0) {
        pg_7578_g(buffer);
    }

    auto* destination = reinterpret_cast<uint8_t*>(
        static_cast<uintptr_t>(buffer->stagingAddress + buffer->tangentOffset));
    if (buffer->packedTangent != 0) {
        const uint32_t packed = packNormPacked32(align16(tangent));
        std::memcpy(destination, &packed, sizeof(packed));
    } else {
        std::memcpy(destination, tangent, buffer->tangentSize);
    }
}
