#include "stm32f10x.h"                  // Device header
#include "PWM.h"

//电机GPIO
#define MOTOR_GPIO1 GPIO_Pin_4
#define MOTOR_GPIO2 GPIO_Pin_5

void Motor_Init()
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Pin =  MOTOR_GPIO1| MOTOR_GPIO2;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    PWM_Init(2000-1,144-1);
}

void Motor_SetSpeed(uint8_t motor,int16_t Speed)
{   if(motor==1) {
        if (Speed > 0) {
            GPIO_SetBits(GPIOA, MOTOR_GPIO1);
            GPIO_ResetBits(GPIOA, MOTOR_GPIO2);
            PWM_SetCompare1(Speed);
        } else {
            GPIO_ResetBits(GPIOA, MOTOR_GPIO1);
            GPIO_SetBits(GPIOA, MOTOR_GPIO2);
            PWM_SetCompare1(-Speed);
        }
    }
    if(motor==2) {
        if (Speed > 0) {
            GPIO_SetBits(GPIOA, MOTOR_GPIO1);
            GPIO_ResetBits(GPIOA, MOTOR_GPIO2);
            PWM_SetCompare2(Speed);
        } else {
            GPIO_ResetBits(GPIOA, MOTOR_GPIO1);
            GPIO_SetBits(GPIOA, MOTOR_GPIO2);
            PWM_SetCompare2(-Speed);
        }
    }
    if(motor==3){
        if (Speed > 0) {
            GPIO_SetBits(GPIOA, MOTOR_GPIO1);
            GPIO_ResetBits(GPIOA, MOTOR_GPIO2);
            PWM_SetCompare2(Speed);
            PWM_SetCompare1(Speed);
        } else {
            GPIO_ResetBits(GPIOA, MOTOR_GPIO1);
            GPIO_SetBits(GPIOA, MOTOR_GPIO2);
            PWM_SetCompare2(-Speed);
            PWM_SetCompare1(-Speed);
        }

    }
}


