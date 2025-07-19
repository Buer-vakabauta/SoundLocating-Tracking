#include "DAC_sound.h"
#include "stm32f4xx_gpio.h"
#include "stm32f4xx_dac.h"
#include "stm32f4xx_tim.h"
#include "stm32f4xx_rcc.h"
#include <math.h>

/**
  * @brief  写入DAC值
  * @param  value: 要写入的值，范围0-4095
  */
void DAC_WriteValue(uint16_t value) 
{
    /* 参数安全检查 */
    if (value > MAX_DAC_VALUE) {
        value = MAX_DAC_VALUE;
    }
    
    /* 写入DAC数据寄存器 */
    DAC->DHR12R1 = value;
}

/**
  * @brief  配置TIM6作为DAC触发源
  */
void TIM6_Config(void) 
{
    TIM_TimeBaseInitTypeDef TIM_InitStruct = {0};
    uint32_t timer_clock = 84000000;  // APB1时钟频率
    uint32_t period = (timer_clock / SAMPLE_RATE) - 1;
    
    /* 1. 使能TIM6时钟 */
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM6, ENABLE);
    
    /* 2. 配置TIM6基础参数 */
    TIM_InitStruct.TIM_Prescaler = 0;
    TIM_InitStruct.TIM_Period = period;
    TIM_InitStruct.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_InitStruct.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInit(TIM6, &TIM_InitStruct);
    
    /* 3. 配置触发输出 */
    TIM_SelectOutputTrigger(TIM6, TIM_TRGOSource_Update);
    
    /* 4. 使能定时器 */
    TIM_Cmd(TIM6, ENABLE);
}

/**
  * @brief  初始化DAC音频输出系统
  */
void DAC_Init_Sound(void) 
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    DAC_InitTypeDef DAC_InitStruct = {0};
    
    /* 1. 使能外设时钟 */
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_DAC, ENABLE);
    
    /* 2. 配置GPIO */
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_4;
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AN;
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_NOPULL;
    GPIO_Init(GPIOA, &GPIO_InitStruct);
    
    /* 3. 配置DAC参数 */
    DAC_InitStruct.DAC_Trigger = DAC_Trigger_T6_TRGO;
    DAC_InitStruct.DAC_WaveGeneration = DAC_WaveGeneration_None;
    DAC_InitStruct.DAC_OutputBuffer = DAC_OutputBuffer_Enable;
    DAC_Init(DAC_Channel_1, &DAC_InitStruct);
    
    /* 4. 使能DAC并设置初始值 */
    DAC_Cmd(DAC_Channel_1, ENABLE);
    DAC_SetChannel1Data(DAC_Align_12b_R, DAC_BIAS);
    
    /* 5. 配置定时器触发 */
    TIM6_Config();
}

/**
  * @brief  生成正弦波数据
  * @param  buffer: 输出缓冲区指针
  * @param  length: 波形数据长度
  * @param  amplitude: 波形振幅(0-2047)
  */
void GenerateSineWave(uint16_t* buffer, uint16_t length, uint16_t amplitude) 
{
    uint16_t i;
    float angle;
    
    /* 参数安全检查 */
    if (amplitude > 2047) {
        amplitude = 2047;
    }
    
    /* 生成正弦波数据 */
    for (i = 0; i < length; i++) {
        angle = 2.0f * M_PI * (float)i / (float)length;
        buffer[i] = DAC_BIAS + (uint16_t)(amplitude * sinf(angle));
    }
}

/**
  * @brief  开始噪声测试(方波输出)
  * @param  freq_hz: 方波频率(Hz)
  * @param  amplitude: 方波振幅(0-2047)
  */
void DAC_StartNoiseTest(uint16_t freq_hz, uint16_t amplitude) 
{
    uint32_t timer_clock = 84000000;
    uint32_t period;
    
    /* 参数安全检查 */
    if (amplitude > 2047) {
        amplitude = 2047;
    }
    
    /* 重新配置TIM6频率 */
    period = (timer_clock / freq_hz) - 1;
    TIM6->ARR = period;
    
    /* 设置方波输出值 */
    DAC->DHR12R1 = DAC_BIAS + amplitude;
    DAC->DHR12R2 = DAC_BIAS - amplitude;
}

