//
// Created by Buer_vakabauta on 2024/10/24.
//

#ifndef ENCODER_H
#define ENCODER_H

#define  TIM3_ARR 65536 - 1
#define  TIM3_PSC 1 - 1

void Encoder_Init_TIM3(void);
void Encoder_Init_TIM4(void);
int16_t Encoder1_Get(void);
int16_t Encoder2_Get(void);

#endif //ENCODER_H
