//
// Created by Buer_vakabauta on 2024/10/23.
//
#include "stm32f10x.h"
#include "ADCconfig.h"

// ADC引脚宏定义
#define ADC1_CH1_PIN GPIO_Pin_3  // ADC1通道1
#define ADC1_CH2_PIN GPIO_Pin_0  // ADC1通道2
#define ADC1_CH3_PIN GPIO_Pin_2  // ADC1通道3

// ADC转换值存储数组
uint16_t ADC_ConvertedValue[3];

void Adc_Init()
{
    ADC_InitTypeDef ADC_InitStructure;
    GPIO_InitTypeDef GPIO_InitStructure;
    DMA_InitTypeDef DMA_InitStructure;
    GPIO_InitTypeDef GPIO_InitStructure1;
    
    // 使能ADC1、GPIOA和DMA1时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_ADC1, ENABLE);
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1, ENABLE);
    RCC_ADCCLKConfig(RCC_PCLK2_Div6);   // 设置ADC分频因子6 72M/6=12,ADC最大时间不能超过14M
    
    // 配置三个ADC输入引脚                                                                                            
    GPIO_InitStructure.GPIO_Pin = ADC1_CH1_PIN | ADC1_CH3_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;  // 模拟输入引脚
    GPIO_InitStructure1.GPIO_Pin = ADC1_CH2_PIN;
    GPIO_InitStructure1.GPIO_Mode = GPIO_Mode_AIN;  // 模拟输入引脚
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    GPIO_Init(GPIOB, &GPIO_InitStructure1);

    // DMA1配置
    DMA_DeInit(DMA1_Channel1);
    DMA_InitStructure.DMA_PeripheralBaseAddr = (uint32_t)&ADC1->DR;  // ADC数据寄存器地址
    DMA_InitStructure.DMA_MemoryBaseAddr = (uint32_t)ADC_ConvertedValue;  // 内存地址
    DMA_InitStructure.DMA_DIR = DMA_DIR_PeripheralSRC;  // 外设作为源
    DMA_InitStructure.DMA_BufferSize = 3;  // 传输3个数据
    DMA_InitStructure.DMA_PeripheralInc = DMA_PeripheralInc_Disable;  // 外设地址不递增
    DMA_InitStructure.DMA_MemoryInc = DMA_MemoryInc_Enable;  // 内存地址递增
    DMA_InitStructure.DMA_PeripheralDataSize = DMA_PeripheralDataSize_HalfWord;  // 16位数据
    DMA_InitStructure.DMA_MemoryDataSize = DMA_MemoryDataSize_HalfWord;  // 16位数据
    DMA_InitStructure.DMA_Mode = DMA_Mode_Circular;  // 循环模式
    DMA_InitStructure.DMA_Priority = DMA_Priority_High;  // 高优先级
    DMA_InitStructure.DMA_M2M = DMA_M2M_Disable;  // 禁止内存到内存传输
    DMA_Init(DMA1_Channel1, &DMA_InitStructure);
    DMA_Cmd(DMA1_Channel1, ENABLE);  // 使能DMA1通道1

    // ADC1配置
    ADC_DeInit(ADC1);  // 复位ADC1
    ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;  // ADC1工作在独立模式
    ADC_InitStructure.ADC_ScanConvMode = ENABLE;  // 使能扫描模式
    ADC_InitStructure.ADC_ContinuousConvMode = ENABLE;  // 使能连续转换模式
    ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;  // 软件触发
    ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;  // 数据右对齐
    ADC_InitStructure.ADC_NbrOfChannel = 3;  // 3个转换通道
    ADC_Init(ADC1, &ADC_InitStructure);

    // 配置规则通道
    ADC_RegularChannelConfig(ADC1, ADC_Channel_2, 1, ADC_SampleTime_239Cycles5);  // 通道1
    ADC_RegularChannelConfig(ADC1, ADC_Channel_3, 2, ADC_SampleTime_239Cycles5);  // 通道2
    ADC_RegularChannelConfig(ADC1, ADC_Channel_8, 3, ADC_SampleTime_239Cycles5);  // 通道3

    // 使能ADC1的DMA
    ADC_DMACmd(ADC1, ENABLE);
    
    ADC_Cmd(ADC1, ENABLE);  // 使能ADC1
    ADC_ResetCalibration(ADC1);  // 复位校准
    while(ADC_GetResetCalibrationStatus(ADC1));  // 等待复位校准结束
    ADC_StartCalibration(ADC1);  // 开始校准
    while(ADC_GetCalibrationStatus(ADC1));  // 等待校准结束
    
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);  // 开始转换
}

// 读取三路ADC值
void ADC_ReadAll(uint16_t* ch1, uint16_t* ch2, uint16_t* ch3)
{
    *ch1 = ADC_ConvertedValue[0];
    *ch2 = ADC_ConvertedValue[1];
    *ch3 = ADC_ConvertedValue[2];
}