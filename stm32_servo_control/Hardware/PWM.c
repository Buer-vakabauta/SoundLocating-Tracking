#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "PWM.h"
#define PWM_GPIO GPIO_Pin_2|GPIO_Pin_3

void PWM_Init(uint16_t ARR, uint16_t PSC)
{
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Pin = PWM_GPIO;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    TIM_InternalClockConfig(TIM2);

    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInitStructure.TIM_Period = ARR;
    TIM_TimeBaseInitStructure.TIM_Prescaler = PSC;
    TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;
    TIM_TimeBaseInit(TIM2, &TIM_TimeBaseInitStructure);
	TIM_ClearFlag(TIM2,TIM_FLAG_Update);//清除更新中断标志位

    TIM_OCInitTypeDef TIM_OCInitStructure;
    TIM_OCStructInit(&TIM_OCInitStructure);
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0;


    TIM_OC3Init(TIM2, &TIM_OCInitStructure);
    TIM_OC4Init(TIM2, &TIM_OCInitStructure);

    TIM_Cmd(TIM2, ENABLE);
}

// 设置占空比函数

void PWM_SetCompare3(uint16_t Compare) { TIM_SetCompare3(TIM2, Compare); }
void PWM_SetCompare4(uint16_t Compare) { TIM_SetCompare4(TIM2, Compare); }

// duty: 0~100 (%)，对应2.5ms~12.5ms在20ms周期中
void PWM3_setDuty(float duty) { TIM_SetCompare3(TIM2, (uint16_t)(duty * 200)); }
void PWM4_setDuty(float duty) { TIM_SetCompare4(TIM2, (uint16_t)(duty * 200)); }

// 设置舵机角度 angle: 0~270
void Servo_setAngle(float v_angle, float h_angle)
{
    if(v_angle >= 0) PWM3_setDuty(2.5 + (v_angle / 270.0f) * 10.0f);
    if(h_angle >= 0) PWM4_setDuty(2.5 + (h_angle / 270.0f) * 10.0f);
}