//
// Created by Buer_vakabauta on 2024/10/30.
//
#include "UART.h"
//#include "cstring"
#include "string.h"

#define BUFFER_SIZE 100

char uart_buffer[BUFFER_SIZE];
uint8_t buffer_index = 0;


void UART_Init(uint32_t baud_rate) {
    // 1. 启用 GPIOA 和 USART1 的时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1 | RCC_APB2Periph_GPIOA, ENABLE);
;
    // 2. 配置 PA9（TX）和 PA10（RX）
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9; // TX
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP; // 复用推挽输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10; // RX
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; // 浮空输入
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 3. 配置 USART 参数
    USART_InitTypeDef USART_InitStructure;
    USART_InitStructure.USART_BaudRate = baud_rate;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART1, &USART_InitStructure);

    //NVIC中断

    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);

    // 配置 NVIC 中断优先级并启用 USART1 中断
    NVIC_InitTypeDef NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);

    // 4. 使能 USART
    USART_Cmd(USART1, ENABLE);
}


void UART_SendChar(char c) {
    USART_SendData(USART1, (uint16_t)c);
    while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET); // 等待发送完成
}

void UART_SendString(const char *str) {
    while (*str) {
        UART_SendChar(*str++);
    }
	UART_SendChar('\n');
}

char UART_ReceiveChar(void) {
    while (USART_GetFlagStatus(USART1, USART_FLAG_RXNE) == RESET); // 等待数据接收
    return (char)USART_ReceiveData(USART1);
}

uint32_t UART_Pow(uint32_t X, uint32_t Y)
{
    uint32_t Result = 1;
    while (Y--)
    {
        Result *= X;
    }
    return Result;
}

void UART_Send_num(int16_t num,uint8_t length){
    if(num<0) UART_SendChar('-');


    for(int i=0;i<length;i++){
        UART_SendChar(num/ UART_Pow(10,length-1-i)%10+'0');
    }
}

void UART_clearBuffer(void) {
    memset(uart_buffer, 0, sizeof(uart_buffer));
    buffer_index = 0;
}



void USART1_IRQHandler(void) {
    if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET) {
        char received_char = (char)USART_ReceiveData(USART1);

        // 检查是否为终止符（例如换行符）
        if (received_char == '\n' || received_char == '\r') {
            uart_buffer[buffer_index] = '\0'; // 字符串结束符
            buffer_index = 0; // 重置索引准备接收下一条数据
            // 在这里处理 uart_buffer 中的数据
        } else if (buffer_index < BUFFER_SIZE - 1) {
            uart_buffer[buffer_index++] = received_char; // 存入缓冲区
        }

        // 清除中断标志位
        USART_ClearITPendingBit(USART1, USART_IT_RXNE);
    }
}



void USART_ReceiveString(void) {
        while (1) {
            char received_char = UART_ReceiveChar();
            // 检查是否为终止符（例如换行符）
            if (received_char == '\n' || received_char == '\r') {
                uart_buffer[buffer_index] = '\0'; // 字符串结束符
                buffer_index = 0; // 重置索引准备接收下一条数据
                break;
                // 在这里处理 uart_buffer 中的数据
            } else if (buffer_index < BUFFER_SIZE - 1) {
                uart_buffer[buffer_index++] = received_char; // 存入缓冲区
            }
        }

}
