#include "stm32f10x.h"                  // Device header
extern  int position=0;
void TCR_Init(){
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IN_FLOATING;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_11;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	
	/*
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_12;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	
	
	
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_15;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	*/
	
	
	
}
/**
  *返回高低点平，黑色，1；白色，0；
  *直行：L=0, m=1, R=0 （仅中间传感器检测到黑色轨迹）
  *急左转：L=1, m=1, R=0 （左传感器检测到黑色轨迹）
  *急右转：L=0, m=1, R=1 （右传感器检测到黑色轨迹）
  *左转：L=1, m=1, R=0 （左传感器和中间传感器都检测到黑色轨迹）
  *右转：L=0, m=1, R=1 （中间传感器和右传感器都检测到黑色轨迹）
  */
uint8_t Read_TCR_Middle(){
    return GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_12);
}
uint8_t Read_TCR_Right(){
     return GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_11);
}
uint8_t Read_TCR_Left(){
      return GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_15);
}

int8_t readsensor(){
    if(Read_TCR_Middle()==1 && Read_TCR_Right()==0 && Read_TCR_Left()==0){position = 0;}//在线上
    if(Read_TCR_Middle()==0 && Read_TCR_Right()==1 && Read_TCR_Left()==0){position = -2;}//急左转
    if(Read_TCR_Middle()==1 && Read_TCR_Right()==1 && Read_TCR_Left()==0){position = -1;}//左转
    if(Read_TCR_Middle()==0 && Read_TCR_Right()==0 && Read_TCR_Left()==1){position = 2;}//急右转
    if(Read_TCR_Middle()==1 && Read_TCR_Right()==0 && Read_TCR_Left()==1){position = 1;}//右转
	if(Read_TCR_Middle()==0 && Read_TCR_Right()==0 && Read_TCR_Left()==0){position = 6;}//停止
    return  position;
}