#include "grc/resource_release.hpp"
// Vertex attribute writes to the Xbox 360's 32-bit vertex-buffer layout.
#include <cstddef>
#include <cstdint>
#include <cstring>
#include "rage/grc_resource_state.hpp"

namespace {

// Partial layout recovered from the attribute accessors around 0x82155B08.
// Addresses stay 32-bit even on a host with 64-bit pointers.
struct PgVertexBuffer {
    uint32_t vertexCount;              // +0x00
    uint8_t pad04[0x04];
    uint32_t formatAddress;             // +0x08: first word is the attribute flags
    uint8_t pad0C[4];
    uint32_t resourceAddress;           // +0x10
    uint8_t pad14[4];
    uint32_t stagingAddress;            // +0x18: one vertex's data, no stride (pg_6B20_g)
    uint32_t dataAddress;               // +0x1C: CPU mapping, refreshed by pg_7578_g
    uint8_t positionOffset;             // +0x20
    uint8_t weightOffset;               // +0x21
    uint8_t indexOffset;                // +0x22
    uint8_t normalOffset;               // +0x23
    uint8_t pad24[0x0A];
    uint8_t tangentOffset;              // +0x2E
    uint8_t pad2F[0x0F];
    uint8_t cpuPositions;               // +0x3E
    uint8_t pad3F[0x1D];
    uint32_t positionSize;              // +0x5C
    uint8_t pad60[0x08];
    uint32_t normalSize;                // +0x68: bytes for the raw-copy format
    uint8_t pad6C[0x28];
    uint32_t tangentSize;               // +0x94: bytes for the raw-copy format
    uint8_t pad98[0x3C];
    uint32_t stride;                    // +0xD4
    uint8_t packedNormal;               // +0xD8
    uint8_t packedTangent;              // +0xD9
    uint8_t padDA;
    uint8_t mapped;                     // +0xDB
    uint32_t mappingThread;              // +0xDC
};

static_assert(offsetof(PgVertexBuffer, resourceAddress) == 0x10);
static_assert(offsetof(PgVertexBuffer, stagingAddress) == 0x18);
static_assert(offsetof(PgVertexBuffer, positionOffset) == 0x20);
static_assert(offsetof(PgVertexBuffer, weightOffset) == 0x21);
static_assert(offsetof(PgVertexBuffer, indexOffset) == 0x22);
static_assert(offsetof(PgVertexBuffer, normalOffset) == 0x23);
static_assert(offsetof(PgVertexBuffer, cpuPositions) == 0x3E);
static_assert(offsetof(PgVertexBuffer, tangentOffset) == 0x2E);
static_assert(offsetof(PgVertexBuffer, positionSize) == 0x5C);
static_assert(offsetof(PgVertexBuffer, normalSize) == 0x68);
static_assert(offsetof(PgVertexBuffer, tangentSize) == 0x94);
static_assert(offsetof(PgVertexBuffer, stride) == 0xD4);
static_assert(offsetof(PgVertexBuffer, packedNormal) == 0xD8);
static_assert(offsetof(PgVertexBuffer, mapped) == 0xDB);
static_assert(offsetof(PgVertexBuffer, mappingThread) == 0xDC);
static_assert(sizeof(PgVertexBuffer) == 0xE0);

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

// vupkd3d128 (NORMPACKED32) turns each signed 10-bit field into 3.0f + n * 2^-22
// (-512 into NaN) and w into 1.0f + its 2 bits; the constants at 0x82034D80
// then scale that back to n / 511 (w: n / 3) with one vnmsubfp.
void unpackNormPacked32(uint32_t packed, float* out) {
    static constexpr float kScale[2] = {-8208.03125f, -2796202.75f};
    static constexpr float kBias[2] = {-24624.09375f, -2796202.75f};
    for (unsigned k = 0; k < 4; ++k) {
        uint32_t bits;
        if (k < 3) {
            const int32_t field = static_cast<int32_t>(packed << (22 - 10 * k)) >> 22;
            bits = field == -512 ? 0x7FC00000u : 0x40400000u + static_cast<uint32_t>(field);
        } else {
            bits = (packed >> 30) | 0x3F800000u;
        }
        float unpacked;
        std::memcpy(&unpacked, &bits, sizeof(unpacked));
        volatile float product = unpacked * kScale[k / 3];
        // -(a*b - c), not c - a*b: the negation also flips NaN and zero signs.
        out[k] = vmxFloat(-(vmxFloat(product) - kBias[k / 3]));
    }
}

const float* align16(const float* p) {
    return reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(p) & ~uintptr_t(15));
}

} // namespace

extern "C" uint8_t pg_7578_g(void* buffer); // @ 0x82157578
extern "C" float* util_5B08(float* result, void* buffer, uint32_t index); // @ 0x82155B08

extern "C" uint8_t g_grcUseResourceLocks; // @ 0x8260640C
extern "C" uint32_t xe_GetCurrentThreadId(); // @ 0x82566B78
extern "C" uint32_t grcResource_Lock(void* resource, uint32_t fence, uint32_t unusedR5,
                                    uint32_t auxiliary, uint32_t base, uint32_t auxiliaryBase,
                                    uint32_t data, uint32_t size, uint32_t flags,
                                    uint32_t cacheFlags); // @ 0x823529E0

// @ 0x82157578 | size: 0xB0
extern "C" uint8_t pg_7578_g(void* vertexBuffer) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    if (!buffer->mapped && buffer->resourceAddress) {
        auto* resource = reinterpret_cast<uint32_t*>(uintptr_t(buffer->resourceAddress));
        const uint32_t data = resource[3] & ~3u;
        if (!g_grcUseResourceLocks) {
            buffer->dataAddress = data;
        } else {
            buffer->dataAddress = grcResource_Lock(resource, resource[1], 0x2E, 0,
                                                   data, 0, data, resource[4] & 0x03FFFFFCu,
                                                   0, 0x03000000u);
        }
        buffer->mapped = 1;
        buffer->mappingThread = xe_GetCurrentThreadId();
    }
    return buffer->mapped;
}

// @ 0x82157628 | size: 0xB8
extern "C" bool grc_7628(void* vertexBuffer) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    if (buffer->mapped) {
        if (buffer->resourceAddress) {
            auto* resource = reinterpret_cast<uint32_t*>(uintptr_t(buffer->resourceAddress));
            if (!rage::g_bTextureEndianDirty && g_grcUseResourceLocks)
                grc_2CC8(resource, resource[3] & ~3u, 0);
#if defined(__powerpc__) || defined(__powerpc64__)
            uint32_t line = buffer->dataAddress & ~127u;
            const uint32_t last = uint32_t(buffer->dataAddress + buffer->stride * buffer->vertexCount - 1) & ~127u;
            do {
                __builtin_ppc_dcbst(reinterpret_cast<void*>(uintptr_t(line)));
                line += 128;
            } while (line <= last);
#else
            // Host GPU backends use coherent CPU mappings; retain ordering.
            __atomic_thread_fence(__ATOMIC_RELEASE);
#endif
        }
        buffer->mapped = 0;
    }
    return buffer->mapped == 0;
}

// Initialize the per-vertex cursor after mapping the underlying resource.
// pg_54B0_g @ 0x821554B0 | size: 0x5C
extern "C" void pg_54B0_g(void* vertexBuffer, uint32_t /*unusedR4*/) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    if (!buffer->mapped) pg_7578_g(buffer);
    buffer->stagingAddress = buffer->dataAddress;
}

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

// Reads the staging vertex's normal back as four floats (unpacked from
// 2:10:10:10 or copied raw); `out` is left alone when there is no normal.
// @ 0x82155BD8
extern "C" float* pg_5BD8_g(float* out, void* vertexBuffer) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    auto* format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    if ((*format & 0x8) == 0) {
        return out;
    }
    if (buffer->mapped == 0) {
        pg_7578_g(buffer);
    }

    const uint32_t source = buffer->stagingAddress + buffer->normalOffset;
    alignas(16) float result[4];
    if (buffer->packedNormal != 0) {
        uint32_t packed;
        std::memcpy(&packed, reinterpret_cast<const void*>(static_cast<uintptr_t>(source)), sizeof(packed));
        unpackNormPacked32(packed, result);
    } else {
        std::memcpy(result, align16(reinterpret_cast<const float*>(static_cast<uintptr_t>(source))),
                    sizeof(result));
    }
    std::memcpy(const_cast<float*>(align16(out)), result, sizeof(result));
    return out;
}

// @ 0x821569C0
extern "C" void grc_69C0(void* vertexBuffer, uint32_t index, const void* position) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    auto* format = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(buffer->formatAddress));
    if ((*format & 0x1) == 0) {
        return;
    }
    if (buffer->mapped == 0) {
        pg_7578_g(buffer);
    }
    const uint32_t offset = buffer->stride * index + buffer->positionOffset;
    std::memcpy(reinterpret_cast<void*>(static_cast<uintptr_t>(buffer->dataAddress + offset)), position,
                buffer->positionSize);
}

namespace {
uint32_t vertexFormat(const PgVertexBuffer* buffer) {
    return *reinterpret_cast<const uint32_t*>(uintptr_t(buffer->formatAddress));
}

void loadStagingVector(float* out, const PgVertexBuffer* buffer, uint32_t offset) {
    const uintptr_t address = uint32_t(buffer->stagingAddress + offset) & ~uintptr_t(15);
    std::memcpy(out, reinterpret_cast<const void*>(address), 16);
}

// The matrix is four row vectors; VMX dot4 accumulates before rounding once.
void skinTransform(float* out, const float* input, const float* matrix) {
    float homogeneous[4];
    for (unsigned lane = 0; lane < 4; ++lane) {
        uint32_t bits, one;
        std::memcpy(&bits, input + lane, 4);
        std::memcpy(&one, lbl_82619BD0 + lane, 4);
        bits = (bits & lbl_82619BE0[lane]) | one;
        std::memcpy(homogeneous + lane, &bits, 4);
    }
    for (unsigned column = 0; column < 3; ++column) {
        double sum = 0.0;
        for (unsigned row = 0; row < 4; ++row)
            sum += double(vmxFloat(homogeneous[row])) * vmxFloat(matrix[row * 4 + column]);
        out[column] = vmxFloat(static_cast<float>(sum));
    }
    // The last merge retains input x in w; it is not a fourth dot product.
    out[3] = homogeneous[0];
}
}

// Skin the source staging vertices into output (or source when output is null).
// r5/r7 are unused slots; r8 is the signed vertex count and r9 the output.
// pg_5510_g @ 0x82155510 | size: 0x4D8
extern "C" void pg_5510_g(void* sourceBuffer, const void* pose, uint32_t /*unusedR5*/,
                           void* skinMap, uint32_t /*unusedR7*/, int32_t vertexCount,
                           void* outputBuffer) {
    auto* source = static_cast<PgVertexBuffer*>(sourceBuffer);
    if (!source->mapped) pg_7578_g(source);
    pg_54B0_g(source, 0);
    auto* output = outputBuffer ? static_cast<PgVertexBuffer*>(outputBuffer) : source;
    if (outputBuffer) pg_54B0_g(output, 0);
    if (vertexCount <= 0) return;
    const auto* palette = static_cast<const uint16_t*>(skinMap);
    const auto* matrices = align16(static_cast<const float*>(pose));
    for (int32_t vertex = 0; vertex < vertexCount; ++vertex) {
        uint32_t indices = ~0u;
        if (vertexFormat(source) & 4) {
            if (!source->mapped) pg_7578_g(source);
            const uintptr_t address = uint32_t(source->stagingAddress + source->indexOffset);
            std::memcpy(&indices, reinterpret_cast<const void*>(address), 4);
        }
        alignas(16) float weights[4] = {};
        if (vertexFormat(source) & 2) {
            if (!source->mapped) pg_7578_g(source);
            loadStagingVector(weights, source, source->weightOffset);
        }
        const uint16_t bones[4] = {palette[(indices >> 16) & 255], palette[(indices >> 8) & 255],
                                   palette[indices & 255], palette[indices >> 24]};
        alignas(16) float blended[16];
        for (unsigned component = 0; component < 16; ++component) {
            float sum = vmxFloat(vmxFloat(matrices[bones[0] * 16 + component]) * vmxFloat(weights[0]));
            for (unsigned influence = 1; influence < 4; ++influence) {
                const float product = vmxFloat(vmxFloat(matrices[bones[influence] * 16 + component]) * vmxFloat(weights[influence]));
                sum = vmxFloat(sum + product);
            }
            blended[component] = sum;
        }
        // PPC's absent position/normal/tangent inputs leave scratch unwritten.
        // Define them as zero; callers must supply an input for each output used.
        alignas(16) float position[4] = {}, normal[4] = {}, tangent[4] = {};
        if (source->cpuPositions) {
            if (!source->mapped) pg_7578_g(source);
            loadStagingVector(position, source, 0);
        }
        pg_5BD8_g(normal, source);
        if (vertexFormat(source) & 0x4000) {
            if (!source->mapped) pg_7578_g(source);
            loadStagingVector(tangent, source, source->tangentOffset);
        }
        alignas(16) float skinnedPosition[4], skinnedNormal[4], skinnedTangent[4];
        skinTransform(skinnedPosition, position, blended);
        skinTransform(skinnedNormal, normal, blended);
        skinTransform(skinnedTangent, tangent, blended);
        if (vertexFormat(output) & 1) {
            if (!output->mapped) pg_7578_g(output);
            const uintptr_t address = uint32_t(output->stagingAddress + output->positionOffset);
            std::memcpy(reinterpret_cast<void*>(address), skinnedPosition, output->positionSize);
        }
        if (vertexFormat(output) & 8) {
            if (!output->mapped) pg_7578_g(output);
            const uintptr_t address = uint32_t(output->stagingAddress + output->normalOffset) & ~uintptr_t(15);
            std::memcpy(reinterpret_cast<void*>(address), skinnedNormal, 16);
        }
        pg_6B20_g(output, 0, skinnedTangent);
        source->stagingAddress += source->stride;
        if (output != source) output->stagingAddress += output->stride;
    }
}

// Indexed normal read. Mapping may replace the data pointer, stride or format.
// util_5B08 @ 0x82155B08 | size: 0xCC
extern "C" float* util_5B08(float* out, void* vertexBuffer, uint32_t index) {
    auto* buffer = static_cast<PgVertexBuffer*>(vertexBuffer);
    if ((vertexFormat(buffer) & 8) == 0) return out;
    if (!buffer->mapped) pg_7578_g(buffer);
    const uint32_t source = buffer->dataAddress + buffer->stride * index + buffer->normalOffset;
    alignas(16) float normal[4];
    if (buffer->packedNormal) {
        uint32_t packed;
        std::memcpy(&packed, reinterpret_cast<const void*>(uintptr_t(source)), 4);
        unpackNormPacked32(packed, normal);
    } else {
        std::memcpy(normal, align16(reinterpret_cast<const float*>(uintptr_t(source))), 16);
    }
    std::memcpy(const_cast<float*>(align16(out)), normal, 16);
    return out;
}
