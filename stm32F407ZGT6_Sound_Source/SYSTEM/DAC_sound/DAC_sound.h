#ifndef DAC_SOUND_H
#define DAC_SOUND_H

#include "stm32f4xx.h"

// 数学常量定义
#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// 音频配置
#define SAMPLE_RATE     44100   // 标准CD音质采样率
#define DAC_BIAS        2048    // 1.65V偏置(3.3V参考电压)
#define MAX_DAC_VALUE   4095    // 12位DAC最大值

// 函数声明
void DAC_WriteValue(uint16_t value);
void TIM6_Config(void);
void DAC_Init_Sound(void);
void GenerateSineWave(uint16_t* buffer, uint16_t length, uint16_t amplitude);
void DAC_StartNoiseTest(uint16_t freq_hz, uint16_t amplitude);

#endif // DAC_SOUND_H

