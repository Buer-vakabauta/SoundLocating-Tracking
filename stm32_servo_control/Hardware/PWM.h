//
// Created by Buer_vakabauta on 2024/10/16.
//
#include "stm32f10x.h"
#ifndef CLIONSTM32DEMO_PWM_H
#define CLIONSTM32DEMO_PWM_H
void PWM_Init(uint16_t  ARR,uint16_t PSC);
void PWM_SetCompare1(uint16_t Compare);
void PWM_SetCompare2(uint16_t Compare);
void PWM2_setDuty(float duty);
void PWM1_setDuty(float duty);
void Servo_setAngle(float v_angle,float h_angle);
#endif //CLIONSTM32DEMO_PWM_H
