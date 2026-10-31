// Replay-driven pose updates of the ball's scene node.
#include "ball_predict.hpp"
#include "ball_visual_spin.hpp"
#include "pong_ball.hpp"

namespace ballReplayUpdate {
struct Instance {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void SetPreviousMatrix(const gmBallNode::Matrix34* matrix) = 0;
    void* archetype;                  // +0x04
    uint16_t levelIndex;              // +0x08
    uint8_t _pad0A[6];
    alignas(16) gmBallNode::Matrix34 matrix; // +0x10
};
struct Level {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Slot3() = 0;
    virtual void Slot4() = 0;
    virtual void Slot5() = 0;
    virtual void Slot6() = 0;
    virtual void Slot7() = 0;
    virtual void Slot8() = 0;
    virtual void Slot9() = 0;
    virtual void Slot10() = 0;
    virtual void UpdateTransform(uint16_t index) = 0;
};
struct Replay {
    uint8_t _pad00000[0xE8F0];
    bpReplayBall current;             // +0x0E8F0, position +0x0E900, spin +0x0E910
    uint8_t _pad0E920[0x68CE4 - 0xE920];
    float time;                       // +0x68CE4
    float previousTime;               // +0x68CE8
};
}

extern "C" void* g_pReplayStateData; // @ 0x8271A2EC
extern void* g_pPhysicsLevel;         // @ 0x826065E4

// @ 0x82282110
void gmBallNode_UpdateReplay(gmBallNode* node) {
    using namespace ballReplayUpdate;
    const auto* replay = static_cast<const Replay*>(g_pReplayStateData);
    const float elapsed = replay->time - replay->previousTime;
    auto* instance = reinterpret_cast<Instance*>(node->inst);
    alignas(16) gmBallNode::Matrix34 matrix = instance->matrix;
    __builtin_memcpy(&matrix.d, &replay->current.pos, sizeof(matrix.d));
    BallNode_IntegrateVisualSpin(node, &replay->current.pos.x, &replay->current.angVel.x,
                                 &matrix.a.x, elapsed);

    instance = reinterpret_cast<Instance*>(node->inst);
    instance->SetPreviousMatrix(&instance->matrix);
    // The virtual can replace the instance and the level; reload both.
    instance = reinterpret_cast<Instance*>(node->inst);
    instance->matrix = matrix;
    auto* level = static_cast<Level*>(g_pPhysicsLevel);
    level->UpdateTransform(reinterpret_cast<Instance*>(node->inst)->levelIndex);
}
