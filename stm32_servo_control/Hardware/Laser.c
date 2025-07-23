#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#define Laser_GPIO GPIO_Pin_1 //PA1
void Laser_Init(){
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Pin = Laser_GPIO;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
}

void Laser_set(uint8_t status){
    if(status>0) GPIO_SetBits(GPIOA,Laser_GPIO);
    else GPIO_ResetBits(GPIOA, Laser_GPIO);
}
