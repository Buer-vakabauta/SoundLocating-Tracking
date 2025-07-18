#ifndef __PID_H
#define __PID_H

#define ZHONGZHI 0
#define position_zero 0
#include "stm32f10x.h"
typedef struct PID_structer {
    int16_t KP, KI, KD;
    int16_t error;
    int16_t last_error;
    int16_t error_sum;
} PID_structer;
void PID_init(PID_structer* PID_);
int16_t Cal_Speed(PID_structer* _PID ,int16_t Target_value,int16_t Current_value);
float Angle_PID(int16_t angle);
int8_t hand_run(int8_t Speedrate,float angle);
float Position_PID(PID_structer *_PID1,int16_t speed,int16_t aim_P);
void auto_run();
void balance_swing();
#endif
