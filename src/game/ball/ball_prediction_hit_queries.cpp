// Queries used by the prediction's hit-outcome classifier.
#include "ball_predict.hpp"
#include <stdint.h>

extern void* g_pTableDims;                    // @ 0x8271A304
extern "C" const float lbl_825C5938;          // @ 0x825C5938

namespace {
struct Table {
    uint8_t _pad00[0x10];
    float width, height, length;
};
uint32_t SignBit(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    return bits >> 31;
}
}

// @ 0x821D8538
int BallPredict_FindNetContact(gdBallPredictData* data, int from) {
    for (int i = from; i < data->m_count; ++i) {
        const gdBallPredictSample& sample = data->At(i);
        if (sample.pos.y <= 0.0f) return -1;
        if (sample.flag9 != 0) return i;
    }
    return -1;
}

// @ 0x821D85D8
int BallPredict_FindReturnAcrossNet(gdBallPredictData* data, int from) {
    const float initialZ = data->At(from).pos.z;
    if (initialZ == 0.0f) return -1;
    const bool wantPositive = initialZ < 0.0f;
    for (int i = from + 1; i < data->m_count; ++i) {
        const gdBallPredictSample& sample = data->At(i);
        if (sample.pos.y <= 0.0f) break;
        if ((sample.pos.z > 0.0f) == wantPositive) return i;
    }
    return -1;
}

// @ 0x821D8440
int BallPredict_FindBounceOnSide(gdBallPredictData* data, uint32_t negativeSide, int from) {
    bool airborne = false;
    for (int i = from; i < data->m_count; ++i) {
        const gdBallPredictSample& sample = data->At(i);
        if (sample.pos.y <= 0.0f) return -1;
        if (sample.bounced == 0) {
            airborne = true;
        } else if (airborne) {
            const uint32_t side = sample.pos.z < 0.0f;
            return side == static_cast<uint8_t>(negativeSide) ? i : -2;
        }
    }
    return -3;
}

// @ 0x821D87E8
int BallPredict_FindDepartingSample(gdBallPredictData* data, int from) {
    if (from >= data->m_count) return -1;
    const auto* table = static_cast<const Table*>(g_pTableDims);
    const float halfWidth = table->width * 0.5f;
    const float negativeHalfWidth = table->width * -0.5f;
    for (int i = from; i < data->m_count; ++i) {
        const gdBallPredictSample& sample = data->At(i);
        if (sample.pos.x > halfWidth && sample.vel.x > 0.0f) return i;
        if (sample.pos.x < negativeHalfWidth && sample.vel.x < 0.0f) return i;
        if (sample.pos.z > table->length * 0.5f && sample.vel.z > 0.0f) return i;
        if (sample.pos.z < table->length * -0.5f && sample.vel.z < 0.0f) return i;
        if (sample.pos.y < table->height && sample.vel.y < 0.0f) return i;
    }
    return -1;
}

// @ 0x821D8AD0
uint32_t BallPredict_NeedsOutcomeForecast(gdBallPredictData* data, uint32_t negativeSide) {
    const auto* table = static_cast<const Table*>(g_pTableDims);
    const gdBallPredictSample& last = data->At(data->m_count - 1);
    if (last.pos.y < table->height - 0.10000000149011612f && last.vel.y < 0.0f) return 0;
    if (SignBit(last.pos.z) == SignBit(last.vel.z)) {
        const float zLimit = __builtin_fmaf(table->length, 0.5f, 0.10000000149011612f);
        if (__builtin_fabsf(last.pos.z) > zLimit) return 0;
        const uint32_t side = last.pos.z < lbl_825C5938;
        if (side != static_cast<uint8_t>(negativeSide)) return 0;
    }
    if (SignBit(last.pos.x) == SignBit(last.vel.x)) {
        const float xLimit = __builtin_fmaf(table->width, 0.5f, 0.10000000149011612f);
        if (__builtin_fabsf(last.pos.x) > xLimit) return 0;
    }
    return 1;
}
