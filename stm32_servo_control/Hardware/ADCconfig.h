//
// Created by Buer_vakabauta on 2024/10/23.
//

#ifndef __ADCCONFIG_H
#define __ADCCONFIG_H

#include "stm32f10x.h"

// 函数声明
void Adc_Init(void);
void ADC_ReadAll(uint16_t* ch1, uint16_t* ch2, uint16_t* ch3);

#endif
