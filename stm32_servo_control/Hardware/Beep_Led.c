#include "stm32f10x.h"                  // Device header
#include "Beep_Led.h"
#include "Delay.h"
void Beep_Led_Init(){
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12 | GPIO_Pin_13;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
}

void low_init(){
    GPIO_SetBits(GPIOB,GPIO_Pin_12);
	GPIO_ResetBits(GPIOB,GPIO_Pin_13);
}

//声光效果
void Beep_led(int delay){
	GPIO_ResetBits(GPIOB, GPIO_Pin_12);
	GPIO_SetBits(GPIOB,GPIO_Pin_13);
    Delay_ms(delay);
	low_init();
}