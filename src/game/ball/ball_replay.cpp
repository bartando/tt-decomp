// Timestamped replay-ball samples: a 900-entry circular queue.
#include "ball_predict.hpp"

namespace {
constexpr int kReplayCapacity = 900;
struct ReplayQueue {
    bpReplayBall samples[kReplayCapacity];
    int32_t head;   // +0xA8C0, newest physical slot
    int32_t tail;   // +0xA8C4, physical slot before the oldest sample
    int32_t count;  // +0xA8C8

    bpReplayBall& At(int index) {
        return samples[(tail + index + 1) % kReplayCapacity];
    }
};
static_assert(__builtin_offsetof(ReplayQueue, head) == 0xA8C0, "replay queue head");
static_assert(__builtin_offsetof(ReplayQueue, count) == 0xA8C8, "replay queue count");
struct ReplayManager {
    uint8_t _pad0000[0x4020];
    ReplayQueue ball;
};

void CopyReplaySample(bpReplayBall& destination, const bpReplayBall& source) {
    // +0x08..0x0F are padding and stay untouched in every copy/shift path.
    __builtin_memcpy(&destination.time, &source.time, 4);
    destination.time2 = source.time2;
    destination.pos = source.pos;
    destination.angVel = source.angVel;
}
}

extern void rage_debugLog(const char* format, ...); // @ 0x8240E6D0
extern "C" const float g_kFloatConst_D108;         // @ 0x8202D108
extern "C" const float g_kFloatConst_D110;         // @ 0x8202D110

// @ 0x821CF1F8
// Moved/corrected from pongLerpQueue_PushFullEntry: this is the 48-byte ball
// replay queue, not the 80-byte player interpolation entry type.
bool BallReplay_AppendSample(void* queuePtr, const bpReplayBall* sample) {
    auto* queue = static_cast<ReplayQueue*>(queuePtr);
    if (queue->count == kReplayCapacity) return false;
    ++queue->head;
    if (queue->head == kReplayCapacity) queue->head = 0;
    CopyReplaySample(queue->samples[queue->head], *sample);
    ++queue->count;
    return true;
}

// @ 0x821CFB60
bool BallReplay_FindNeighborIndices(void* queuePtr, void* /*unusedR4*/, int* first,
                                    int* second, float* factor, float time) {
    auto* queue = static_cast<ReplayQueue*>(queuePtr);
    const int count = queue->count;
    if (count == 0) {
        rage_debugLog("pongLerpQueue::FindNeighborIndices - queue is empty!");
        return false;
    }
    if (count < 2) {
        rage_debugLog("Lerp Queue GetCount<2");
        *first = 0;
        *second = 0;
        *factor = g_kFloatConst_D110;
        return true;
    }
    if (time < queue->At(0).time) {
        rage_debugLog("Lerp Queue t<GetMinT()");
        *first = 0;
        *factor = g_kFloatConst_D110;
        *second = 1;
        return true;
    }
    if (time > queue->At(count - 1).time) {
        rage_debugLog("Lerp Queue t>GetMaxT()");
        const int endCount = queue->count;
        *factor = g_kFloatConst_D108;
        *first = endCount - 2;
        *second = endCount - 1;
        return true;
    }
    for (int i = 0; i < count - 1; ++i) {
        if (queue->At(i).time <= time && queue->At(i + 1).time >= time) {
            const float duration = queue->At(i + 1).time - queue->At(i).time;
            *factor = duration > g_kFloatConst_D110
                ? (time - queue->At(i).time) / duration : g_kFloatConst_D108;
            *first = i;
            *second = i + 1;
            return true;
        }
    }
    return true;
}

// @ 0x821CF298
void BallReplay_InsertSample(void* queuePtr, int index, const bpReplayBall* sample) {
    auto* queue = static_cast<ReplayQueue*>(queuePtr);
    BallReplay_AppendSample(queue, &queue->At(queue->count - 1));
    for (int i = queue->count - 2; i > index; --i) {
        CopyReplaySample(queue->At(i), queue->At(i - 1));
    }
    // Do not snapshot the source before shifting: it can alias the ring.
    CopyReplaySample(queue->At(index), *sample);
}

// @ 0x821CE780
void BallReplay_InsertTimedSample(void* queuePtr, const bpReplayBall* sample) {
    auto* queue = static_cast<ReplayQueue*>(queuePtr);
    const int count = queue->count;
    if (count != 0) {
        const float time = sample->time;
        const int tail = queue->tail;
        if (!(time > queue->At(count - 1).time)) {
            if (count == 1) {
                // A NaN also takes this insertion branch (blt, then bns).
                if (!(time >= queue->At(0).time)) {
                    BallReplay_InsertSample(queue, 0, sample);
                    return;
                }
            } else {
                int first;
                int second = -1;
                float factor;
                BallReplay_FindNeighborIndices(queue, nullptr, &first, &second, &factor, time);
                // Keep the tail/count cached across the neighbor lookup, as the
                // original does. Skip every existing sample with this timestamp.
                while (second < count && time == queue->samples[(tail + second + 1) % kReplayCapacity].time) {
                    ++second;
                }
                if (second != count) {
                    BallReplay_InsertSample(queue, second, sample);
                    return;
                }
            }
        }
    }
    BallReplay_AppendSample(queue, sample);
}

// @ 0x821CD0F8
void gdReplayMgr_RecordBallSample(void* replayPtr, bpReplayBall* sample) {
    auto* replay = static_cast<ReplayManager*>(replayPtr);
    ReplayQueue* queue = &replay->ball;
    if (queue->count == kReplayCapacity) {
        ++queue->tail;
        --queue->count;
        if (queue->tail == kReplayCapacity) queue->tail = 0;
    }
    BallReplay_InsertTimedSample(queue, sample);
}

// @ 0x821CE910
void BallReplay_RemoveSample(void* queuePtr, int index) {
    auto* queue = static_cast<ReplayQueue*>(queuePtr);
    for (int next = index + 1; next < queue->count; ++next) {
        CopyReplaySample(queue->At(next - 1), queue->At(next));
    }
    --queue->count;
    queue->head = queue->head == 0 ? kReplayCapacity - 1 : queue->head - 1;
}
