// Ball prediction outcome flags: direct classification and forecast recovery.
#include "ball_predict.hpp"
#include <cmath>

extern void* g_game_state_ptr;                      // @ 0x8271A2F8
extern void* g_pongMatchTiming;                     // @ 0x8271A2E8
extern void* g_input_obj_ptr;                       // @ 0x825EAB28
extern int32_t g_currentInputSlot;                  // @ 0x82606578
extern "C" uint8_t g_ballSplashArray[832];          // @ 0x8261A3D0
extern "C" float g_ballRecoveryHalfWidth;          // @ 0x825C7554
extern "C" float g_ballRecoveryHalfLength;         // @ 0x825C7558
extern void nop_8240E6D0(const char* format, ...);    // @ 0x8240E6D0
extern int BallPredict_FindNetContact(gdBallPredictData* data, int from); // @ 0x821D8538
extern int BallPredict_FindReturnAcrossNet(gdBallPredictData* data, int from); // @ 0x821D85D8
extern int BallPredict_FindBounceOnSide(gdBallPredictData* data, uint32_t negativeSide, int from); // @ 0x821D8440
extern int BallPredict_FindDepartingSample(gdBallPredictData* data, int from); // @ 0x821D87E8
extern uint32_t BallPredict_NeedsOutcomeForecast(gdBallPredictData* data, uint32_t negativeSide); // @ 0x821D8AD0
extern void BallPredict_MarkHittableWindow(void* state, int unusedBank, int from, int count, int flag); // @ 0x821D38E8
extern void BallPredict_MarkLateTableExit(int unusedBank, void* idsArray, int from); // @ 0x8228A4E8
extern void BallPredict_ForecastOutcome(gdBallPredictSample* sample, int* result, int unusedBank); // @ 0x8228A688

namespace {
struct State { uint8_t _pad00[0x14]; gdBallPredictData* prediction; };
struct Clock { uint8_t _pad00[0x30]; float now; };

State* CurrentState() { return static_cast<State*>(g_game_state_ptr); }
float Now() { return static_cast<Clock*>(g_pongMatchTiming)->now; }

void CopySample(gdBallPredictSample& out, const gdBallPredictSample& in) {
    out.time = in.time;
    out.time2 = in.time2;
    out.bounced = in.bounced;
    out.flag9 = in.flag9;
    out.hittable = in.hittable;
    out.pos = in.pos;
    out.vel = in.vel;
    out.angVel = in.angVel;
    out.orient = in.orient;
}
}

// @ 0x82289B10
void BallPredict_BuildHitIds(int /*unusedBank*/) {
    State* state = CurrentState();
    gdBallPredictData* data = state->prediction;
    const int originalCount = data->m_count;
    const uint32_t positiveSide = data->At(0).pos.z > 0.0f;
    const uint32_t shotOffset = static_cast<uint32_t>(g_currentInputSlot) * 0x1A0u;
    uint16_t shotFlags;
    __builtin_memcpy(&shotFlags, g_ballSplashArray + shotOffset + 0xF6, 2);
    int found = 0;
    if ((shotFlags & 0x1000) != 0) {
        found = BallPredict_FindNetContact(data, 0);
        if (found >= 0) {
            data->m_ids[0] |= 1;
            data->m_ids[0] |= 2;
            data->m_idTime = data->At(found).time;
            if (BallPredict_FindReturnAcrossNet(data, found) < 0) data->m_ids[0] |= 8;
            return;
        }
        found = BallPredict_FindBounceOnSide(data, positiveSide == 0, 0);
        if (found < 0) {
            if (found == -1 || found == -3) {
                found = BallPredict_FindDepartingSample(data, 0);
            } else if (found == -2) {
                found = BallPredict_FindBounceOnSide(data, positiveSide, 0);
            } else {
                return;
            }
            if (found >= 0) {
                data->m_ids[0] |= 1;
                data->m_ids[0] |= 2;
                data->m_idTime = data->At(found).time;
            }
            return;
        }
    }
    const int from = found + 1;
    found = BallPredict_FindBounceOnSide(data, positiveSide, from);
    if (found >= 0) {
        BallPredict_MarkHittableWindow(state, 1, found + 1, originalCount, 1);
        return;
    }
    if (found == -1 || found == -3) {
        found = BallPredict_FindDepartingSample(data, from);
    } else if (found == -2) {
        found = BallPredict_FindBounceOnSide(data, positiveSide == 0, from);
    } else {
        return;
    }
    if (found >= 0) {
        data->m_ids[0] |= 1;
        data->m_ids[0] |= 2;
        data->m_idTime = data->At(found).time;
        const int net = BallPredict_FindNetContact(data, from);
        if (net > 0 && BallPredict_FindReturnAcrossNet(data, net) < 0) data->m_ids[0] |= 8;
    }
}

// @ 0x82289E90
void BallPredict_RecoverHitIds(int /*unusedBank*/) {
    gdBallPredictData* data = CurrentState()->prediction;
    const int first = data->FindFirstHittable();
    if (first > 0) {
        const int end = data->FindFirstUnhittableFrom(first + 1);
        if (end > 0) {
            if (data->At(end).bounced != 0) {
                data->m_ids[0] |= 1;
                data->m_ids[0] &= ~2u;
                data->m_ids[0] |= 4;
                data->m_idTime = data->At(end).time;
            } else {
                data->m_ids[0] |= 1;
                data->m_ids[0] &= ~2u;
                data->m_idTime = Now();
                BallPredict_MarkLateTableExit(1, &data->m_ids, first);
            }
            return;
        }
        const uint32_t negativeSide = data->At(first).pos.z < 0.0f;
        const uint32_t needsForecast = BallPredict_NeedsOutcomeForecast(data, negativeSide);
        if (static_cast<uint8_t>(needsForecast) == 0) {
            data->m_ids[0] |= 1;
            data->m_idTime = Now();
            BallPredict_MarkLateTableExit(1, &data->m_ids, first);
            return;
        }

        nop_8240E6D0("This used to be an \"outcome unknown)\" situation.");
        gdBallPredictSample forecast;
        CopySample(forecast, data->At(data->m_count - 1));
        int outcome = 0;
        BallPredict_ForecastOutcome(&forecast, &outcome, 1);
        data->m_ids[0] |= 1;
        data->m_ids[0] &= ~2u;
        data->m_idTime = data->At(first).time;
        switch (outcome) {
        case 0:
            nop_8240E6D0("This shot may end up being a double-table bounce or dinker, but we're not marking it as such.");
            break;
        case 1: case 2:
            data->m_ids[0] |= 4;
            break;
        case 3:
            if (__builtin_fabsf(forecast.pos.x) < g_ballRecoveryHalfWidth &&
                __builtin_fabsf(forecast.pos.z) < g_ballRecoveryHalfLength) {
                data->m_ids[0] |= 16;
            }
            break;
        default:
            break;
        }
        return;
    }

    const uint32_t opponent = g_currentInputSlot == 0;
    const uint32_t negativeSide = static_cast<const uint8_t*>(g_input_obj_ptr)[0x40 + opponent] == 0;
    const uint32_t needsForecast = BallPredict_NeedsOutcomeForecast(data, negativeSide);
    if (static_cast<uint8_t>(needsForecast) == 0) {
        data->m_ids[0] |= 1;
        data->m_ids[0] |= 2;
        data->m_idTime = data->At(data->m_count - 1).time;
        return;
    }

    nop_8240E6D0("This used to be an \"outcome unknown)\" situation.  Extrapolating an outcome...");
    nop_8240E6D0("(This shot may end up being a double-table bounce or dinker, but we're not marking it as such.)");
    gdBallPredictSample forecast;
    CopySample(forecast, data->At(data->m_count - 1));
    int outcome = 0;
    BallPredict_ForecastOutcome(&forecast, &outcome, 1);
    if (outcome == 0) return;
    bool otherSide = false;
    if (outcome == 3) otherSide = true;
    else if (outcome == 1) otherSide = negativeSide != 0;
    else if (outcome == 2) otherSide = negativeSide == 0;
    data->m_ids[0] |= 1;
    if (otherSide) data->m_ids[0] |= 2;
    else data->m_ids[0] &= ~2u;
    data->m_idTime = forecast.time;
}
