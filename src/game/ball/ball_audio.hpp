#pragma once

void BallAudio_SetEmitterPosition(void* emitter,const float* position); // @ 0x82160C98
void BallAudio_SetEmitterGain(void* emitter,float gain); // @ 0x82162218

int BallAudio_PreImpact(void* audio,void* unusedR4,int kind,const float* position,int index,float energy); // @ 0x8228AD58
