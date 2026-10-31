// Creature pose snapshots and worker reset, recovered from the original PPC.
#include <cstdint>
#include <cstring>
#include "pong_creature.hpp"
#include "rage/mat44.hpp"

namespace {
float flushPoseFloat(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

// VMX dot3 accumulates the three products before rounding to a float.
float poseDot3(const float* vector, const float* matrix, unsigned column) {
    double sum = 0.0;
    for (unsigned axis = 0; axis < 3; ++axis)
        sum += double(flushPoseFloat(vector[axis])) * flushPoseFloat(matrix[axis * 4 + column]);
    return flushPoseFloat(static_cast<float>(sum));
}
}

// Copy the current pose, compensating translation for each bone's rest position.
// LocomotionState_CD70_g @ 0x8214CD70 | size: 0x118
extern "C" void LocomotionState_CD70_g(void* skeleton, void* poseSnapshot) {
    const auto* bytes = static_cast<const uint8_t*>(skeleton);
    const auto* data = *reinterpret_cast<const uint8_t* const*>(bytes + 4);
    const auto* banks = *reinterpret_cast<const uint8_t* const* const*>(bytes + 0x18);
    const unsigned bank = *reinterpret_cast<const uint16_t*>(bytes + 0x22);
    const auto* matrices = banks[bank * 2];
    const int count = *reinterpret_cast<const uint16_t*>(data + 0x0C);
    auto* output = static_cast<uint8_t*>(poseSnapshot);
    for (int bone = count - 1; bone >= 0; --bone) {
        const auto* overrideData = *reinterpret_cast<const uint8_t* const*>(bytes + 0x24);
        const auto* rest = overrideData
            ? *reinterpret_cast<const uint8_t* const*>(overrideData + 4) + bone * 16
            : *reinterpret_cast<const uint8_t* const*>(data) + bone * 0xC0 + 0x50;
        alignas(16) float restPosition[4];
        std::memcpy(restPosition, rest, sizeof(restPosition));
        const auto* source = matrices + bone * 64;
        auto* target = output + bone * 64;
        // Preserve the original's row-by-row load/store order for overlaps.
        for (unsigned row = 0; row < 3; ++row)
            std::memcpy(target + row * 16, source + row * 16, 16);
        const auto* matrix = reinterpret_cast<const float*>(source);
        const float x = poseDot3(restPosition, matrix, 0);
        const float y = poseDot3(restPosition, matrix, 1);
        const float z = poseDot3(restPosition, matrix, 2);
        const float offsets[4] = {x, y, z, x};
        alignas(16) float translation[4];
        std::memcpy(translation, source + 0x30, sizeof(translation));
        auto* targetTranslation = reinterpret_cast<float*>(target + 0x30);
        for (unsigned lane = 0; lane < 4; ++lane)
            targetTranslation[lane] = flushPoseFloat(flushPoseFloat(translation[lane]) - offsets[lane]);
    }
}

struct pongCreatureWorker;
struct pongCreatureSkeleton;

extern "C" uint32_t g_creatureWorkerRelativePose; // @ 0x825C9F54
extern "C" uint32_t g_renderClearRingIdx; // @ 0x82606348
extern "C" void pg_5510_g(void* destination, const void* pose, uint32_t boneCount,
                           void* skinMap, uint32_t unusedR7, int32_t vertexCount,
                           void* source); // @ 0x82155510
extern "C" uint8_t pg_7578_g(void* buffer); // @ 0x82157578
extern "C" bool grc_7628(void* buffer); // @ 0x82157628

namespace {
template<class T> T& workerField(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

struct WorkerResetBound {
    virtual void slot0() = 0;
    virtual void vfn_1(uint32_t flag) = 0;
};
}

// Snapshot the skeleton, optionally remove the mesh root transform, skin the
// vertices, copy their positions into both worker arrays, then reset bounds.
// pongCreatureWorker_Reset (was pg_AB78_g) @ 0x820FAB78 | size: 0x2C0
void pongCreatureWorker_Reset(pongCreatureWorker* worker, pongCreatureSkeleton* skeleton) {
    void* geometry = workerField<void*>(worker, 0x3C);
    void* skeletonData = workerField<void*>(geometry, 8);
    const uint32_t boneCount = workerField<uint16_t>(skeletonData, 0x0C);
    auto* matrices = static_cast<float*>(__builtin_alloca(boneCount * 64));
    LocomotionState_CD70_g(skeleton, matrices);
    geometry = workerField<void*>(worker, 0x3C);
    const uint32_t meshSlot = workerField<uint32_t>(worker, 0x40);
    const uint32_t meshIndex = workerField<uint32_t>(worker, 0x44);
    const uint32_t batchIndex = workerField<uint32_t>(worker, 0x48);
    void* meshTable = reinterpret_cast<void**>(geometry)[meshSlot + 16];
    void* mesh = workerField<void**>(meshTable, 0)[meshIndex];
    auto* batch = workerField<uint8_t*>(mesh, 4) + uint32_t(batchIndex * 40);
    if (g_creatureWorkerRelativePose) {
        alignas(16) float inverse[16];
        const uint8_t rootBone = workerField<uint8_t>(mesh, 0x13);
        std::memcpy(inverse, matrices + rootBone * 16, sizeof(inverse));
        pongCreatureInst::CopyAndBuildTranslationMatrix(inverse);
        for (uint32_t bone = 0; bone < boneCount; ++bone)
            rage::mat44ComposeAffineInPlace(matrices + bone * 16, inverse);
    }
    const uint32_t bufferIndex = workerField<uint8_t>(batch, 0x25) ? g_renderClearRingIdx : 0;
    void* bufferSet = workerField<void*>(batch, 0);
    void* buffer = reinterpret_cast<void**>(bufferSet)[bufferIndex];
    void* skinMap = workerField<void*>(bufferSet, 0x38);
    const int32_t vertexCount = workerField<int32_t>(buffer, 0);
    pg_5510_g(workerField<void*>(worker, 0x6C), matrices, boneCount, skinMap, 0, vertexCount, buffer);
    // PPC starts with unwritten scratch; CPU fetches initialize only xyz.
    // Define those initial lanes as zero; unavailable later reads retain xyz.
    alignas(16) float position[4] = {};
    for (int32_t vertex = 0; vertex < workerField<int32_t>(buffer, 0); ++vertex) {
        if (workerField<uint8_t>(buffer, 0x3E)) {
            if (!workerField<uint8_t>(buffer, 0xDB)) pg_7578_g(buffer);
            const uint32_t stride = workerField<uint32_t>(buffer, 0xD4);
            const auto* data = workerField<const uint8_t*>(buffer, 0x1C);
            std::memcpy(position, data + uint32_t(stride * vertex), 12);
        }
        const uint32_t index = workerField<const uint32_t*>(worker, 0x28)[vertex];
        void* part = workerField<void*>(worker, 0x24);
        std::memcpy(workerField<uint8_t*>(part, 0x24) + uint32_t(index * 16), position, 16);
        std::memcpy(workerField<uint8_t*>(part, 0x1C) + uint32_t(index * 16), position, 16);
    }
    grc_7628(workerField<void*>(worker, 0x6C));
    grc_7628(buffer);
    void* part = workerField<void*>(worker, 0x24);
    void* root = workerField<void*>(part, 0);
    if (!root) return;
    void* archetype = workerField<void*>(root, 4);
    if (!archetype) return;
    auto* bound = workerField<WorkerResetBound*>(archetype, 0x0C);
    if (!bound || workerField<uint8_t>(bound, 4) != 9) return;
    bound->vfn_1(1);
    for (uint32_t i = 0; i < workerField<uint16_t>(part, 0x104); ++i) {
        const uint32_t index = workerField<const uint32_t*>(part, 0x100)[i];
        workerField<WorkerResetBound**>(bound, 0x70)[index]->vfn_1(1);
    }
}
